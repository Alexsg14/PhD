"""
server.py — MD Simulation Dashboard
FastAPI backend with WebSocket for real-time monitoring.
"""

import asyncio
import json
import os
import time
import signal
import sys
from contextlib import asynccontextmanager

def sigint_handler(signum, frame):
    print("\n🧬 [Dashboard] Shutdown requested. Terminating immediately...")
    os._exit(0)

signal.signal(signal.SIGINT, sigint_handler)


import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

SYSTEM_PATTERN = re.compile(r"^(TEAD|YAP)_[a-zA-Z0-9_-]+$")
STEP_PATTERN = re.compile(r"^(step\d+_eq|tray)$")

from gromacs_parser import scan_all_systems, get_log_summary
from realtime_analysis import compute_analyses, extract_last_frame_pdb, extract_trajectory_pdb, VIEWER_DIR

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(VIEWER_DIR, exist_ok=True)

# Cache for analysis results
analysis_cache = {}
pdb_cache_time = {}
systems_cache = {"data": [], "timestamp": 0}

# Performance tracker: { "SYSTEM_r1": { "last_sim_ps": float, "last_wall": float, "ns_per_day_live": float } }
log_perf_tracker = {}

SCAN_INTERVAL = 15        # seconds between system scans
ANALYSIS_INTERVAL = 300   # 5 min between trajectory analyses
PDB_INTERVAL = 600        # 10 min between PDB extractions


def compute_live_ns_per_day(system: str, replica: int, log_data: dict) -> dict:
    """
    Estimate ns/day from the sim-time delta between log reads.
    Returns two values:
      - ns_per_day_recent: rolling estimate of the current simulation speed
        (delta between last two reads, smoothed with exponential moving average)
      - ns_per_day_cumulative: average since the first time this log was seen
        (total sim-time elapsed / total wall time elapsed, ignores queue pauses
         because the numerator is sim-time, not wall-clock)
    """
    key = f"{system}_r{replica}"
    new_sim_ps = log_data.get("last_sim_time_ps")
    new_wall = log_data.get("log_read_wall_time")

    empty = {"ns_per_day_recent": None, "ns_per_day_cumulative": None}
    if new_sim_ps is None or new_wall is None:
        return empty

    prev = log_perf_tracker.get(key)
    if prev is None:
        # First reading — store anchor point and wait for next cycle
        log_perf_tracker[key] = {
            "last_sim_ps": new_sim_ps,
            "last_wall": new_wall,
            "first_sim_ps": new_sim_ps,
            "first_wall": new_wall,
            "ns_per_day_recent": None,
            "ns_per_day_cumulative": None,
        }
        return empty

    delta_ps = new_sim_ps - prev["last_sim_ps"]
    delta_wall_s = new_wall - prev["last_wall"]

    # ── Recent estimate (delta between last two reads) ──────────
    recent = prev.get("ns_per_day_recent")
    if delta_ps > 0 and delta_wall_s > 5:
        instant = (delta_ps / 1000.0) / (delta_wall_s / 86400.0)
        recent = (0.3 * instant + 0.7 * recent) if recent is not None else instant
        recent = round(recent, 2)

    # ── Cumulative estimate (total sim-time / total wall-time since first read) ──
    # Note: wall time here IS affected by queue, but the numerator (sim_ps
    # actually simulated) stays at zero during queue → ratio naturally goes
    # toward zero if the simulation was queued for a long time at the start.
    # To avoid penalizing for queue time, we reset the anchor point to the
    # moment the log first showed any sim-time > its initial value (i.e.
    # the moment the simulation actually started running on the node).
    cumulative = prev.get("ns_per_day_cumulative")
    if delta_ps > 0:
        # Anchor: if first_sim_ps equals new_sim_ps, the sim was idle since we
        # first saw it — keep anchor at the first moment it advanced.
        if prev["first_sim_ps"] == prev["last_sim_ps"]:
            # Sim just started moving: reset anchor to right now
            log_perf_tracker[key]["first_sim_ps"] = prev["last_sim_ps"]
            log_perf_tracker[key]["first_wall"] = prev["last_wall"]

        total_ps = new_sim_ps - log_perf_tracker[key]["first_sim_ps"]
        total_wall_s = new_wall - log_perf_tracker[key]["first_wall"]
        if total_ps > 0 and total_wall_s > 5:
            cumulative = round((total_ps / 1000.0) / (total_wall_s / 86400.0), 2)

    log_perf_tracker[key].update({
        "last_sim_ps": new_sim_ps,
        "last_wall": new_wall,
        "ns_per_day_recent": recent,
        "ns_per_day_cumulative": cumulative,
    })
    return {"ns_per_day_recent": recent, "ns_per_day_cumulative": cumulative}


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_scanner())
    yield
    task.cancel()


app = FastAPI(title="MD Dashboard", lifespan=lifespan)


# ── API Endpoints ──────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/favicon.ico")
async def favicon():
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🧬</text></svg>'
    from fastapi.responses import Response
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/systems")
async def api_systems():
    if time.time() - systems_cache["timestamp"] > SCAN_INTERVAL:
        systems_cache["data"] = await asyncio.to_thread(scan_all_systems)
        systems_cache["timestamp"] = time.time()
    return JSONResponse(systems_cache["data"])


def validate_system_and_step(system: str, step: str = None):
    if not SYSTEM_PATTERN.match(system):
        raise HTTPException(status_code=400, detail="Invalid system name pattern")
    if step is not None and not STEP_PATTERN.match(step):
        raise HTTPException(status_code=400, detail="Invalid step name pattern")


@app.get("/api/log/{system}/{replica}")
async def api_log(system: str, replica: int):
    validate_system_and_step(system)
    data = await asyncio.to_thread(get_log_summary, system, replica)
    if data is None:
        return JSONResponse({"error": "No log data available"}, status_code=404)
    return JSONResponse(data)


class CancelToken:
    def __init__(self):
        self.cancelled = False


@app.get("/api/analysis/{system}/{replica}")
async def api_analysis(system: str, replica: int, is_cancelled=None):
    validate_system_and_step(system)
    cache_key = f"{system}_r{replica}"
    cached = analysis_cache.get(cache_key)
    if cached and time.time() - cached["timestamp"] < ANALYSIS_INTERVAL:
        return JSONResponse(cached["data"])

    # Find the system info
    systems = systems_cache.get("data") or await asyncio.to_thread(scan_all_systems)
    target = None
    for s in systems:
        if s["system"] == system and s["replica"] == replica:
            target = s
            break

    if not target or not target.get("xtc_path"):
        return JSONResponse({"error": "No trajectory data"}, status_code=404)

    data = await asyncio.to_thread(
        compute_analyses, target["pdb_path"], target["xtc_path"], 5, True, is_cancelled
    )
    if data is None:
        return JSONResponse({"error": "Analysis failed"}, status_code=500)

    analysis_cache[cache_key] = {"data": data, "timestamp": time.time()}
    return JSONResponse(data)


@app.get("/api/analysis_full/{system}/{replica}")
async def api_analysis_full(system: str, replica: int, is_cancelled=None):
    validate_system_and_step(system)
    cache_key = f"{system}_r{replica}_full"
    cached = analysis_cache.get(cache_key)
    if cached and time.time() - cached["timestamp"] < ANALYSIS_INTERVAL:
        return JSONResponse(cached["data"])

    systems = systems_cache.get("data") or await asyncio.to_thread(scan_all_systems)
    target = None
    for s in systems:
        if s["system"] == system and s["replica"] == replica:
            target = s
            break

    if not target or not target.get("available_steps"):
        return JSONResponse({"error": "No trajectory data available"}, status_code=404)

    # Sanitize each step in target["available_steps"] before path construction
    for step in target["available_steps"]:
        validate_system_and_step(system, step)

    xtc_paths = [os.path.join(target["replica_dir"], f"r{replica}_{step}.xtc") for step in target["available_steps"]]

    data = await asyncio.to_thread(
        compute_analyses, target["pdb_path"], xtc_paths, 5, True, is_cancelled
    )
    if data is None:
        return JSONResponse({"error": "Full analysis failed"}, status_code=500)

    analysis_cache[cache_key] = {"data": data, "timestamp": time.time()}
    return JSONResponse(data)


@app.get("/api/analysis_step/{system}/{replica}/{step}")
async def api_analysis_step(system: str, replica: int, step: str, is_cancelled=None):
    validate_system_and_step(system, step)
    cache_key = f"{system}_r{replica}_{step}"
    cached = analysis_cache.get(cache_key)
    # We can cache specific steps longer if they are completed, but for now use same interval
    if cached and time.time() - cached["timestamp"] < ANALYSIS_INTERVAL:
        return JSONResponse(cached["data"])

    systems = systems_cache.get("data") or await asyncio.to_thread(scan_all_systems)
    target = None
    for s in systems:
        if s["system"] == system and s["replica"] == replica:
            target = s
            break

    if not target:
        return JSONResponse({"error": "System not found"}, status_code=404)

    xtc_path = os.path.join(target["replica_dir"], f"r{replica}_{step}.xtc")
    if not os.path.exists(xtc_path):
        return JSONResponse({"error": f"Trajectory for {step} not found"}, status_code=404)

    data = await asyncio.to_thread(
        compute_analyses, target["pdb_path"], xtc_path, 5, True, is_cancelled
    )
    if data is None:
        return JSONResponse({"error": "Step analysis failed"}, status_code=500)

    analysis_cache[cache_key] = {"data": data, "timestamp": time.time()}
    return JSONResponse(data)


@app.get("/api/extract_pdb/{system}/{replica}")
async def api_extract_pdb(system: str, replica: int):
    validate_system_and_step(system)
    systems = systems_cache.get("data") or await asyncio.to_thread(scan_all_systems)
    target = None
    for s in systems:
        if s["system"] == system and s["replica"] == replica:
            target = s
            break

    if not target or not target.get("xtc_path"):
        return JSONResponse({"error": "No trajectory"}, status_code=404)

    path = await asyncio.to_thread(
        extract_last_frame_pdb,
        target["pdb_path"], target["xtc_path"], system, replica
    )
    if path is None:
        return JSONResponse({"error": "PDB extraction failed"}, status_code=500)

    return JSONResponse({"pdb_url": f"/viewer/{os.path.basename(path)}"})


@app.get("/api/extract_trajectory/{system}/{replica}")
async def api_extract_trajectory(system: str, replica: int):
    validate_system_and_step(system)
    systems = systems_cache.get("data") or await asyncio.to_thread(scan_all_systems)
    target = None
    for s in systems:
        if s["system"] == system and s["replica"] == replica:
            target = s
            break

    if not target or not target.get("xtc_path"):
        return JSONResponse({"error": "No trajectory"}, status_code=404)

    path = await asyncio.to_thread(
        extract_trajectory_pdb,
        target["pdb_path"], target["xtc_path"], system, replica
    )
    if path is None:
        return JSONResponse({"error": "Trajectory extraction failed"}, status_code=500)

    return JSONResponse({"pdb_url": f"/viewer/{os.path.basename(path)}"})


# ── WebSocket ──────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    active_cancel_token = None
    active_target = None

    async def handle_analysis_request(msg_type, system, replica, step=None):
        nonlocal active_cancel_token, active_target
        target = (msg_type, system, replica, step)
        
        if active_target == target:
            return  # Same task is already running, let it continue

        if active_cancel_token:
            active_cancel_token.cancelled = True
            
        token = CancelToken()
        active_cancel_token = token
        active_target = target
        
        def check_cancelled():
            return token.cancelled
            
        try:
            if msg_type == "get_analysis":
                resp = await api_analysis(system, replica, is_cancelled=check_cancelled)
                if token.cancelled:
                    return
                body = json.loads(resp.body.decode())
                await ws.send_json({
                    "type": "analysis_data",
                    "system": system,
                    "replica": replica,
                    "data": body
                })
            elif msg_type == "get_analysis_full":
                resp = await api_analysis_full(system, replica, is_cancelled=check_cancelled)
                if token.cancelled:
                    return
                body = json.loads(resp.body.decode())
                await ws.send_json({
                    "type": "analysis_full_data",
                    "system": system,
                    "replica": replica,
                    "data": body
                })
            elif msg_type == "get_analysis_step":
                resp = await api_analysis_step(system, replica, step, is_cancelled=check_cancelled)
                if token.cancelled:
                    return
                body = json.loads(resp.body.decode())
                await ws.send_json({
                    "type": "analysis_step_data",
                    "system": system,
                    "replica": replica,
                    "step": step,
                    "data": body
                })
        except Exception as e:
            print(f"⚠️ [WS] Error in analysis task: {e}")
        finally:
            if active_target == target:
                active_target = None

    try:
        # Send initial systems list
        systems = await asyncio.to_thread(scan_all_systems)
        systems_cache["data"] = systems
        systems_cache["timestamp"] = time.time()
        await ws.send_json({"type": "systems", "data": systems})

        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            print(f"📥 [WS Message] Received: {msg.get('type')} for {msg.get('system')} r{msg.get('replica')}")

            if "system" in msg:
                if not SYSTEM_PATTERN.match(msg["system"]):
                    print(f"⚠️ [WS] Invalid system name pattern in message: {msg['system']}")
                    continue
            if "step" in msg:
                if not STEP_PATTERN.match(msg["step"]):
                    print(f"⚠️ [WS] Invalid step name pattern in message: {msg['step']}")
                    continue

            if msg.get("type") == "get_systems":
                systems = await asyncio.to_thread(scan_all_systems)
                systems_cache["data"] = systems
                systems_cache["timestamp"] = time.time()
                await ws.send_json({"type": "systems", "data": systems})

            elif msg.get("type") == "get_log":
                log_data = await asyncio.to_thread(
                    get_log_summary, msg["system"], msg["replica"]
                )
                if log_data:
                    # Compute both live ns/day estimates (recent + cumulative)
                    perf = compute_live_ns_per_day(msg["system"], msg["replica"], log_data)
                    log_data["ns_per_day_recent"] = perf["ns_per_day_recent"]
                    log_data["ns_per_day_cumulative"] = perf["ns_per_day_cumulative"]
                await ws.send_json({
                    "type": "log_data",
                    "system": msg["system"],
                    "replica": msg["replica"],
                    "data": log_data
                })

            elif msg.get("type") == "get_analysis":
                asyncio.create_task(handle_analysis_request("get_analysis", msg["system"], msg["replica"]))

            elif msg.get("type") == "get_analysis_full":
                asyncio.create_task(handle_analysis_request("get_analysis_full", msg["system"], msg["replica"]))

            elif msg.get("type") == "get_analysis_step":
                asyncio.create_task(handle_analysis_request("get_analysis_step", msg["system"], msg["replica"], msg["step"]))

            elif msg.get("type") == "get_pdb":
                resp = await api_extract_pdb(msg["system"], msg["replica"])
                body = json.loads(resp.body.decode())
                await ws.send_json({
                    "type": "pdb_ready",
                    "system": msg["system"],
                    "replica": msg["replica"],
                    "data": body
                })

            elif msg.get("type") == "get_trajectory_pdb":
                resp = await api_extract_trajectory(msg["system"], msg["replica"])
                body = json.loads(resp.body.decode())
                await ws.send_json({
                    "type": "trajectory_pdb_ready",
                    "system": msg["system"],
                    "replica": msg["replica"],
                    "data": body
                })

    except WebSocketDisconnect:
        manager.disconnect(ws)
        if active_cancel_token:
            active_cancel_token.cancelled = True
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(ws)
        if active_cancel_token:
            active_cancel_token.cancelled = True


# ── Background Scanner ─────────────────────────────────────────

async def background_scanner():
    """Periodically scan systems and broadcast updates."""
    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL)
            systems = await asyncio.to_thread(scan_all_systems)
            systems_cache["data"] = systems
            systems_cache["timestamp"] = time.time()
            await manager.broadcast({"type": "systems", "data": systems})
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Scanner error: {e}")
            await asyncio.sleep(5)


# ── Static file serving ────────────────────────────────────────

app.mount("/viewer", StaticFiles(directory=VIEWER_DIR), name="viewer")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\n🧬 MD Simulation Dashboard")
    print("   Open http://localhost:8080 in your browser\n")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
