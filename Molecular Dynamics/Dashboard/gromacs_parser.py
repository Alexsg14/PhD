"""
gromacs_parser.py
Parses GROMACS .log files and scans simulation directory structure.
READ-ONLY: never writes to the simulation directories.
"""

import os
import re
import glob
import time
from pathlib import Path

# Base directory with all simulations - configurable via environment variable
BASE_DIR = os.environ.get("MD_DASHBOARD_BASE_DIR", "/home/ciqus/aliciaft3/YAP_TEAD_Junio26")

# Step definitions: (name_pattern, dt_ps, nsteps, duration_ns)
STEP_INFO = {}
for i in range(1, 14):
    if i == 1:
        STEP_INFO[f"step{i}_eq"] = {"dt": 0.001, "nsteps": 8000000, "duration_ns": 8.0}
    elif i == 2:
        STEP_INFO[f"step{i}_eq"] = {"dt": 0.001, "nsteps": 8000000, "duration_ns": 8.0}
    else:
        STEP_INFO[f"step{i}_eq"] = {"dt": 0.002, "nsteps": 4000000, "duration_ns": 8.0}
STEP_INFO["tray"] = {"dt": 0.002, "nsteps": 50000000, "duration_ns": 100.0}


def parse_log_energies(log_path):
    """
    Parse a GROMACS .log file to extract time-series of energies.
    Returns dict with lists of values for each energy term.
    """
    if not os.path.exists(log_path):
        return None

    result = {
        "steps": [], "times": [],
        "temperature": [], "pressure": [], "potential": [],
        "total_energy": [], "kinetic_energy": [],
        "nsteps": None, "dt": None,
    }

    try:
        with open(log_path, "r", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None

    # Extract dt and nsteps from header
    for line in lines[:400]:
        m = re.match(r"\s+dt\s+=\s+([\d.eE+-]+)", line)
        if m:
            result["dt"] = float(m.group(1))
        m = re.match(r"\s+nsteps\s+=\s+(\d+)", line)
        if m:
            result["nsteps"] = int(m.group(1))

    # Parse energy blocks
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Detect "Step    Time" header
        if re.match(r"Step\s+Time", line):
            i += 1
            if i < len(lines):
                parts = lines[i].split()
                if len(parts) >= 2:
                    try:
                        step = int(parts[0])
                        time_val = float(parts[1])
                        result["steps"].append(step)
                        result["times"].append(time_val)
                    except ValueError:
                        pass
            # Now look for energy values in following lines
            # Handles two log formats:
            #   Equilibration: "Temperature   Pressure" on one line, values on next
            #   Production:    "Potential  Kinetic En.  Total Energy  Conserved En.  Temperature"
            #                  followed by values, then "Pres. DC (bar)  Pressure (bar)..."
            for j in range(i + 1, min(i + 25, len(lines))):
                hdr = lines[j].strip()

                # ── Case 1 (equilibration): Temperature and Pressure on same header line ──
                if "Temperature" in hdr and "Pressure" in hdr:
                    if j + 1 < len(lines):
                        vals = lines[j + 1].split()
                        if len(vals) >= 3:
                            try:
                                result["temperature"].append(float(vals[0]))
                                result["pressure"].append(float(vals[2]))
                            except (ValueError, IndexError):
                                pass

                # ── Case 2 (production): "Potential  Kinetic En.  Total Energy  Conserved En.  Temperature" ──
                elif "Potential" in hdr and "Kinetic" in hdr and "Total Energy" in hdr:
                    if j + 1 < len(lines):
                        vals = lines[j + 1].split()
                        # Production format (4 or 5 values): Potential Kinetic Total Conserved [Temperature]
                        # Equilibration format (5 values):   PosRest Potential Kinetic Total Conserved
                        if "Temperature" in hdr:
                            # Production: Temperature is last column in this row
                            try:
                                result["potential"].append(float(vals[0]))
                                result["kinetic_energy"].append(float(vals[1]))
                                result["total_energy"].append(float(vals[2]))
                                if len(vals) >= 5:
                                    result["temperature"].append(float(vals[4]))
                            except (ValueError, IndexError):
                                pass
                        else:
                            # Equilibration: Position_Rest Potential Kinetic Total Conserved
                            try:
                                result["potential"].append(float(vals[1]))
                                result["kinetic_energy"].append(float(vals[2]))
                                result["total_energy"].append(float(vals[3]))
                            except (ValueError, IndexError):
                                pass

                # ── Case 2b (production): "Pres. DC (bar)  Pressure (bar)..." ──
                elif "Pressure (bar)" in hdr and "Pres. DC" in hdr:
                    # Columns: Pres.DC  Pressure  dVcoul/dl  dVvdw/dl  Constr.rmsd
                    if j + 1 < len(lines):
                        vals = lines[j + 1].split()
                        if len(vals) >= 2:
                            try:
                                result["pressure"].append(float(vals[1]))
                            except (ValueError, IndexError):
                                pass
        i += 1

    return result


def parse_performance(log_path):
    """
    Parse the final Performance block from a GROMACS .log file.
    This block only exists when the simulation has finished or been interrupted.
    Returns dict with ns_per_day and hours_per_ns, or None if not found.
    """
    if not os.path.exists(log_path):
        return None
    try:
        # Only read the last 80 lines — Performance block is always at the end
        with open(log_path, "r", errors="replace") as f:
            tail = f.readlines()[-80:]
    except Exception:
        return None

    result = {}
    in_perf = False
    for line in tail:
        if line.lstrip().startswith("Time:"):
            # Format: Time:   328615.394    20538.463     1600.0
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    result["wall_time_s"] = float(parts[2])
                except ValueError:
                    pass
            continue
            
        if re.match(r"\s*Performance:", line):
            m = re.search(r"Performance:\s+([\d.]+)\s+([\d.]+)", line)
            if m:
                result["ns_per_day"] = float(m.group(1))
                result["hours_per_ns"] = float(m.group(2))
            return result
    return result if result else None

def get_log_start_time(log_path):
    """
    Parse the start time from the 'Started mdrun' line near the beginning of the log.
    Returns the start time as a unix timestamp, or None if not found.
    """
    if not os.path.exists(log_path):
        return None
    try:
        with open(log_path, "r", errors="replace") as f:
            for _ in range(1000): # Usually in the first 500 lines
                line = f.readline()
                if not line: break
                if "Started mdrun" in line:
                    # e.g., "Started mdrun on rank 0 Mon Jun  8 13:33:48 2026"
                    parts = line.strip().split("Started mdrun on rank 0 ")
                    if len(parts) == 2:
                        time_str = parts[1].strip()
                        # Parse time string: Mon Jun  8 13:33:48 2026
                        import time
                        try:
                            # strptime format: %a %b %d %H:%M:%S %Y
                            # Sometimes day is single digit with 2 spaces
                            time_str = re.sub(r'\s+', ' ', time_str)
                            return time.mktime(time.strptime(time_str, "%a %b %d %H:%M:%S %Y"))
                        except ValueError:
                            return None
        return None
    except Exception:
        return None

def get_log_status(log_path):
    if not os.path.exists(log_path):
        return "pending"
    # If log hasn't been modified in 15 minutes (900s), it is stopped
    if time.time() - os.path.getmtime(log_path) > 900:
        return "stopped"
    return "running"

def get_replica_wall_time(replica_dir, replica_num):
    """
    Calculate the total time spent on this replica.
    Returns a tuple: (effective_time, calendar_time)
      - effective_time: sum of actual compute time (ignoring SLURM queue times)
      - calendar_time: absolute time elapsed since the very first step started
    """
    effective_time = 0.0
    prefix = f"r{replica_num}_"
    
    log_files = []
    for i in range(1, 14):
        log_files.append(os.path.join(replica_dir, f"{prefix}step{i}_eq.log"))
    log_files.append(os.path.join(replica_dir, f"{prefix}tray.log"))

    first_start_time = None
    last_mod_time = 0
    is_running = False
    
    last_known_hours_per_ns = 3.0 # Fallback default

    for log_path in log_files:
        if os.path.exists(log_path):
            # For calendar time tracking
            start_time = get_log_start_time(log_path)
            if start_time and first_start_time is None:
                first_start_time = start_time
            
            mtime = os.path.getmtime(log_path)
            if mtime > last_mod_time:
                last_mod_time = mtime
                
            status = get_log_status(log_path)
            if status == "running":
                is_running = True

            # For effective time tracking: Use simulation time estimate to account for SLURM restarts
            # (Because restarted chunks don't record their wall time in the final Performance block)
            perf = parse_performance(log_path)
            log_data = parse_log_energies(log_path)
            
            if perf and "hours_per_ns" in perf:
                last_known_hours_per_ns = perf["hours_per_ns"]
                
            if log_data and log_data["times"] and len(log_data["times"]) > 1:
                total_ps = log_data["times"][-1] - log_data["times"][0]
                total_ns = total_ps / 1000.0
                effective_time += total_ns * last_known_hours_per_ns * 3600
            else:
                # Fallback if no simulation data
                if start_time:
                    if status == "running":
                        effective_time += max(0, time.time() - start_time)
                    else:
                        effective_time += max(0, os.path.getmtime(log_path) - start_time)
    
    calendar_time = 0.0
    if first_start_time is not None:
        end_time = time.time() if is_running else last_mod_time
        calendar_time = max(0, end_time - first_start_time)

    return effective_time, calendar_time

def detect_active_step(replica_dir, replica_num):
    """
    Detect which simulation step is currently active in a replica directory.
    Returns dict with step info.
    """
    prefix = f"r{replica_num}_"
    
    # Check production first
    tray_log = os.path.join(replica_dir, f"{prefix}tray.log")
    tray_gro = os.path.join(replica_dir, f"{prefix}tray.gro")
    if os.path.exists(tray_gro):
        return {"step": "tray", "status": "completed", "phase": "production",
                "log": tray_log, "xtc": os.path.join(replica_dir, f"{prefix}tray.xtc")}
    if os.path.exists(tray_log):
        return {"step": "tray", "status": get_log_status(tray_log), "phase": "production",
                "log": tray_log, "xtc": os.path.join(replica_dir, f"{prefix}tray.xtc")}

    # Check equilibration steps (13 down to 1)
    last_completed = 0
    active_step = None
    for i in range(13, 0, -1):
        step_name = f"step{i}_eq"
        gro = os.path.join(replica_dir, f"{prefix}{step_name}.gro")
        log = os.path.join(replica_dir, f"{prefix}{step_name}.log")
        xtc = os.path.join(replica_dir, f"{prefix}{step_name}.xtc")

        if os.path.exists(gro):
            last_completed = max(last_completed, i)
        elif os.path.exists(log):
            active_step = {
                "step": step_name, "status": get_log_status(log),
                "phase": "equilibration", "step_num": i,
                "log": log, "xtc": xtc
            }

    if active_step:
        return active_step

    if last_completed > 0:
        # Last completed step but next hasn't started
        if last_completed < 13:
            next_step = last_completed + 1
            return {"step": f"step{next_step}_eq", "status": "pending",
                    "phase": "equilibration", "step_num": next_step,
                    "last_completed": f"step{last_completed}_eq"}
        else:
            return {"step": "tray", "status": "pending", "phase": "production",
                    "last_completed": "step13_eq"}

    # Check if step 1 has any files at all
    step1_log = os.path.join(replica_dir, f"{prefix}step1_eq.log")
    if os.path.exists(step1_log):
        return {"step": "step1_eq", "status": get_log_status(step1_log), "phase": "equilibration",
                "step_num": 1, "log": step1_log,
                "xtc": os.path.join(replica_dir, f"{prefix}step1_eq.xtc")}

    return {"step": "step1_eq", "status": "pending", "phase": "equilibration", "step_num": 1}


def get_progress(log_data, step_name):
    """Calculate progress percentage from log data and step info."""
    if not log_data or not log_data["steps"]:
        return 0.0, 0, 0

    current_step = log_data["steps"][-1]
    nsteps = log_data.get("nsteps") or STEP_INFO.get(step_name, {}).get("nsteps", 1)
    progress = min(100.0, (current_step / nsteps) * 100.0) if nsteps > 0 else 0.0
    return progress, current_step, nsteps


def get_step_posres(replica_num, step_name):
    """Parse the .mdp file to get the position restraints applied."""
    if step_name == "tray":
        return "None (Production)"
        
    mdp_path = os.path.join(BASE_DIR, f"MDPs_replica_{replica_num}", f"{step_name}.mdp")
    if not os.path.exists(mdp_path):
        return "Unknown"
        
    try:
        with open(mdp_path, "r") as f:
            for line in f:
                if line.strip().startswith("define"):
                    parts = line.split("=", 1)
                    if len(parts) > 1:
                        restraints = parts[1].strip()
                        if not restraints or restraints == "-DPOSRES":
                            return "Standard Restraints"
                            
                        nice_parts = []
                        for r in restraints.split():
                            if r == "-DPOSRES": continue
                            r = r.replace("-DPOSRES_", "")
                            if "=" in r:
                                k, v = r.split("=", 1)
                                nice_parts.append(f"{k}: {v}")
                            else:
                                nice_parts.append(r)
                        
                        if nice_parts:
                            return " | ".join(nice_parts)
                        return "Standard Restraints"
        return "None"
    except Exception:
        return "Unknown"


def scan_all_systems():
    """
    Scan BASE_DIR for all TEAD_*/YAP_* systems and their replicas.
    Returns list of system status dicts.
    """
    systems = []
    
    for system_dir in sorted(glob.glob(os.path.join(BASE_DIR, "TEAD_*")) +
                             glob.glob(os.path.join(BASE_DIR, "YAP_*"))):
        system_name = os.path.basename(system_dir)
        if not os.path.isdir(system_dir):
            continue

        for rep_num in [1, 2, 3]:
            replica_dir = os.path.join(system_dir, f"replica_{rep_num}")
            if not os.path.isdir(replica_dir):
                continue

            step_info = detect_active_step(replica_dir, rep_num)
            
            # Get topology PDB
            pdb_path = os.path.join(replica_dir, "complex_with_ligand.pdb")
            if not os.path.exists(pdb_path):
                pdb_path = os.path.join(system_dir, "complex_with_ligand.pdb")

            # Parse log if available
            log_data = None
            progress = 0.0
            current_step_num = 0
            total_steps = 0
            if step_info.get("log") and os.path.exists(step_info["log"]):
                log_data = parse_log_energies(step_info["log"])
                progress, current_step_num, total_steps = get_progress(
                    log_data, step_info["step"])

            # Calculate overall progress (across all 14 steps)
            completed_steps = 0
            available_steps = []
            all_posres = {}
            for si in range(1, 14):
                step_name = f"step{si}_eq"
                gro = os.path.join(replica_dir, f"r{rep_num}_{step_name}.gro")
                xtc = os.path.join(replica_dir, f"r{rep_num}_{step_name}.xtc")
                if os.path.exists(gro):
                    completed_steps += 1
                if os.path.exists(xtc):
                    available_steps.append(step_name)
                    all_posres[step_name] = get_step_posres(rep_num, step_name)
                    
            tray_gro = os.path.join(replica_dir, f"r{rep_num}_tray.gro")
            tray_xtc = os.path.join(replica_dir, f"r{rep_num}_tray.xtc")
            if os.path.exists(tray_gro):
                completed_steps += 1
            if os.path.exists(tray_xtc):
                available_steps.append("tray")
                all_posres["tray"] = get_step_posres(rep_num, "tray")

            overall_progress = (completed_steps * 100.0 + progress) / 14.0

            systems.append({
                "system": system_name,
                "replica": rep_num,
                "replica_dir": replica_dir,
                "pdb_path": pdb_path,
                "step": step_info["step"],
                "status": step_info["status"],
                "phase": step_info["phase"],
                "step_progress": round(progress, 1),
                "current_step_num": current_step_num,
                "total_steps": total_steps,
                "overall_progress": round(overall_progress, 1),
                "posres": get_step_posres(rep_num, step_info["step"]),
                "all_posres": all_posres,
                "completed_steps": completed_steps,
                "available_steps": available_steps,
                "log_path": step_info.get("log"),
                "xtc_path": step_info.get("xtc"),
                "has_log_data": log_data is not None and len(log_data.get("steps", [])) > 0,
            })

    return systems

def get_log_summary(system_name, replica_num):
    """Get detailed log data for a specific system/replica."""
    replica_dir = os.path.join(BASE_DIR, system_name, f"replica_{replica_num}")
    step_info = detect_active_step(replica_dir, replica_num)
    
    if not step_info.get("log") or not os.path.exists(step_info["log"]):
        return None

    log_data = parse_log_energies(step_info["log"])
    if not log_data:
        return None

    progress, current, total = get_progress(log_data, step_info["step"])

    # Performance: try to read final block (simulation completed/interrupted)
    perf = parse_performance(step_info["log"])

    # Last sim time (ps) from the log — used by server to estimate live ns/day
    last_sim_time_ps = log_data["times"][-1] if log_data["times"] else None

    # Step wall time: estimate from simulation time to handle SLURM restarts
    step_wall_time_s = 0.0
    if log_data and log_data["times"] and len(log_data["times"]) > 1:
        total_ps = log_data["times"][-1] - log_data["times"][0]
        total_ns = total_ps / 1000.0
        # If the step hasn't finished, we don't have perf["hours_per_ns"]. 
        # We assume ~3.0 hours/ns (typical for this system) or use the perf if available.
        h_per_ns = perf["hours_per_ns"] if (perf and "hours_per_ns" in perf) else 3.0
        step_wall_time_s = total_ns * h_per_ns * 3600
    else:
        start_time = get_log_start_time(step_info["log"])
        if start_time:
            if step_info["status"] == "running":
                step_wall_time_s = max(0, time.time() - start_time)
            else:
                step_wall_time_s = max(0, os.path.getmtime(step_info["log"]) - start_time)

    replica_eff_time_s, replica_cal_time_s = get_replica_wall_time(replica_dir, replica_num)

    return {
        "step": step_info["step"],
        "status": step_info["status"],
        "phase": step_info["phase"],
        "progress": round(progress, 1),
        "current_step": current,
        "total_steps": total,
        "times": log_data["times"],
        "temperature": log_data["temperature"],
        "pressure": log_data["pressure"],
        "potential": log_data["potential"],
        "total_energy": log_data["total_energy"],
        # Performance data
        "ns_per_day_final": perf["ns_per_day"] if perf else None,
        "hours_per_ns_final": perf["hours_per_ns"] if perf else None,
        "last_sim_time_ps": last_sim_time_ps,
        "log_read_wall_time": time.time(),   # wall clock when this was read
        "step_wall_time_s": step_wall_time_s,
        "replica_wall_time_s": replica_eff_time_s,
        "replica_calendar_time_s": replica_cal_time_s,
    }
