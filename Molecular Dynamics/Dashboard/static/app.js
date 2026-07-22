/* ═══════════════════════════════════════════════════════════════
   MD Simulation Dashboard — Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────

let ws = null;
let systems = [];
let selectedSystem = null;
let selectedReplica = null;
let charts = {};
let chartsFull = {};
let viewer3d = null;
let currentFilter = "all";
let reconnectTimer = null;
let scanCountdown = 60;

// ── Chart.js Global Config ────────────────────────────────────

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.animation.duration = 600;

const CHART_COLORS = {
    rmsd: "#8b5cf6",
    rg: "#06b6d4",
    com: "#10b981",
    contacts: "#f59e0b",
    temperature: "#ef4444",
    fel: "#8b5cf6",
};

// ── WebSocket Connection ──────────────────────────────────────

function connectWS() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => {
        setConnectionStatus("connected", "Connected");
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
    };

    ws.onclose = () => {
        setConnectionStatus("error", "Disconnected");
        reconnectTimer = setTimeout(connectWS, 3000);
    };

    ws.onerror = () => {
        setConnectionStatus("error", "Error");
    };
}

function setConnectionStatus(state, text) {
    const dot = document.querySelector("#connection-status .status-dot");
    const txt = document.querySelector("#connection-status .status-text");
    dot.className = "status-dot " + state;
    txt.textContent = text;
}

function sendWS(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
    }
}

// ── Message Handler ───────────────────────────────────────────

function handleMessage(msg) {
    switch (msg.type) {
        case "systems":
            systems = msg.data;
            renderSidebar();
            renderOverview();
            updateActiveCount();
            // Auto-refresh detail if viewing
            if (selectedSystem && selectedReplica) {
                const sys = systems.find(s => s.system === selectedSystem && s.replica === selectedReplica);
                if (sys) updateProgressSection(sys);
            }
            break;

        case "log_data":
            if (msg.system === selectedSystem && msg.replica === selectedReplica && msg.data) {
                updateEnergyPanel(msg.data);
                updateTemperatureChart(msg.data);
            }
            break;

        case "analysis_data":
        case "analysis_step_data":
            if (msg.system === selectedSystem && msg.replica === selectedReplica && msg.data) {
                updateAnalysisCharts(msg.data);
                if (msg.type === "analysis_step_data") {
                    document.getElementById("detail-step").textContent = "Step: " + msg.step;
                    const sys = systems.find(s => s.system === selectedSystem && s.replica === selectedReplica);
                    if (sys && sys.all_posres) {
                        document.getElementById("stat-posres").textContent = sys.all_posres[msg.step] || "Unknown";
                    }
                } else {
                    const sys = systems.find(s => s.system === selectedSystem && s.replica === selectedReplica);
                    if (sys) {
                        const stepLabel = sys.step.replace("_eq", "").replace("step", "Step ").replace("tray", "Production");
                        document.getElementById("detail-step").textContent = `${stepLabel} · ${sys.phase}`;
                        document.getElementById("stat-posres").textContent = sys.posres || "Unknown";
                    }
                }
            }
            break;

        case "analysis_full_data":
            if (msg.system === selectedSystem && msg.replica === selectedReplica && msg.data) {
                updateFullAnalysisCharts(msg.data);
                document.getElementById("full-system-name").textContent = `${msg.system} · Replica ${msg.replica}`;
            }
            break;

        case "pdb_ready":
            if (msg.data && msg.data.pdb_url) {
                loadPDB(msg.data.pdb_url, false);
            }
            break;

        case "trajectory_pdb_ready":
            if (msg.data && msg.data.pdb_url) {
                loadPDB(msg.data.pdb_url, true);
            }
            break;
    }
}

// ── Sidebar Rendering ─────────────────────────────────────────

function renderSidebar() {
    const container = document.getElementById("systems-list");
    if (!systems.length) {
        container.innerHTML = `<div class="loading-placeholder"><p>No simulations found</p></div>`;
        return;
    }

    // Group by system name
    const groups = {};
    systems.forEach(s => {
        if (!groups[s.system]) groups[s.system] = [];
        groups[s.system].push(s);
    });

    let html = "";
    for (const [name, replicas] of Object.entries(groups)) {
        // Apply filter
        const filtered = replicas.filter(r => {
            if (currentFilter === "all") return true;
            if (currentFilter === "running") return r.status === "running";
            if (currentFilter === "completed") return r.status === "completed";
            return true;
        });
        if (filtered.length === 0) continue;

        const shortName = name.replace("TEAD_", "T·").replace("YAP_", "Y·");
        html += `<div class="system-group-label">${shortName}</div>`;

        filtered.forEach(r => {
            const isSelected = r.system === selectedSystem && r.replica === selectedReplica;
            const stepLabel = r.step.replace("_eq", "").replace("step", "S").replace("tray", "PROD");
            html += `
                <div class="sim-card ${isSelected ? 'selected' : ''}"
                     data-system="${r.system}" data-replica="${r.replica}"
                     data-status="${r.status}">
                    <div class="sim-status-icon ${r.status}"></div>
                    <div class="sim-info">
                        <div class="sim-name">${name} · R${r.replica}</div>
                        <div class="sim-detail">${stepLabel} · ${r.step_progress}%</div>
                    </div>
                    <div class="sim-progress-mini">
                        <div class="sim-progress-mini-bar" style="width: ${r.overall_progress}%"></div>
                    </div>
                </div>`;
        });
    }

    container.innerHTML = html;

    // Attach click handlers
    container.querySelectorAll(".sim-card").forEach(card => {
        card.addEventListener("click", () => {
            selectSimulation(card.dataset.system, parseInt(card.dataset.replica));
        });
    });
}

function updateActiveCount() {
    const running = systems.filter(s => s.status === "running").length;
    document.getElementById("active-count").textContent = `${running} active`;
}

// ── Overview Grid ─────────────────────────────────────────────

function renderOverview() {
    const grid = document.getElementById("overview-grid");
    if (!systems.length) { grid.innerHTML = ""; return; }

    grid.innerHTML = systems.map(s => {
        const stepLabel = s.step.replace("_eq", "").replace("step", "Step ").replace("tray", "Production");
        const statusColor = s.status === "running" ? "var(--green)" : s.status === "completed" ? "var(--cyan)" : "var(--text-muted)";
        return `
            <div class="overview-card" data-system="${s.system}" data-replica="${s.replica}">
                <div class="ov-name" style="color: ${statusColor}">${s.system} · R${s.replica}</div>
                <div class="ov-step">${stepLabel} — ${s.status}</div>
                <div class="ov-progress-bar">
                    <div class="ov-progress-fill" style="width: ${s.overall_progress}%"></div>
                </div>
            </div>`;
    }).join("");

    grid.querySelectorAll(".overview-card").forEach(card => {
        card.addEventListener("click", () => {
            selectSimulation(card.dataset.system, parseInt(card.dataset.replica));
        });
    });
}

// ── Simulation Selection ──────────────────────────────────────

function selectSimulation(system, replica) {
    selectedSystem = system;
    selectedReplica = replica;

    document.getElementById("welcome-screen").classList.add("hidden");
    document.getElementById("full-traj-view").classList.add("hidden");
    document.getElementById("detail-view").classList.remove("hidden");

    // Update header
    document.getElementById("detail-system-name").textContent = `${system} · Replica ${replica}`;

    // Find system info
    const sys = systems.find(s => s.system === system && s.replica === replica);
    if (sys) {
        const stepLabel = sys.step.replace("_eq", "").replace("step", "Step ").replace("tray", "Production");
        document.getElementById("detail-step").textContent = `${stepLabel} · ${sys.phase}`;
        updateProgressSection(sys);

        // Populate step selector
        const selector = document.getElementById("step-selector");
        selector.innerHTML = '<option value="active">Active Step</option>';
        if (sys.available_steps) {
            sys.available_steps.forEach(step => {
                const label = step.replace("_eq", "").replace("step", "Step ").replace("tray", "Production");
                selector.innerHTML += `<option value="${step}">${label}</option>`;
            });
        }
    }

    // Re-render sidebar selection
    renderSidebar();

    // Clear previous charts and viewer
    destroyCharts();
    initCharts();

    // Clear 3D viewer placeholder
    const viewerContainer = document.getElementById("mol-viewer");
    viewerContainer.innerHTML = '<div class="viewer-placeholder"><p>Loading structure...</p></div>';
    document.getElementById("viewer-badge").textContent = "Loading...";
    if (viewer3d) {
        viewer3d.clear();
        viewer3d = null;
    }

    // Request data automatically
    sendWS({ type: "get_analysis", system, replica });
    sendWS({ type: "get_log", system, replica });
    sendWS({ type: "get_pdb", system, replica });
}

function goBack() {
    selectedSystem = null;
    selectedReplica = null;
    document.getElementById("welcome-screen").classList.remove("hidden");
    document.getElementById("detail-view").classList.add("hidden");
    document.getElementById("full-traj-view").classList.add("hidden");
    renderSidebar();
    destroyCharts();
    destroyFullCharts();
}

// ── Progress Section ──────────────────────────────────────────

function updateProgressSection(sys) {
    const stepLabel = sys.step.replace("_eq", "").replace("step", "Step ").replace("tray", "Production");
    document.getElementById("stat-step-progress").textContent = sys.step_progress + "%";
    document.getElementById("stat-current-step").textContent = stepLabel;
    document.getElementById("stat-overall").textContent = sys.overall_progress + "%";
    document.getElementById("stat-phase").textContent = sys.phase;
    document.getElementById("stat-posres").textContent = sys.posres || "Unknown";
    document.getElementById("progress-bar").style.width = sys.step_progress + "%";
}

function flipEnergyCard(cardId, event = null) {
    if (event) event.stopPropagation();
    const flipper = document.getElementById(cardId);
    if (flipper) {
        flipper.classList.toggle("flipped");
    }
}

// ── Energy Panel ──────────────────────────────────────────────

function updateEnergyPanel(data) {
    if (!data) return;
    const lastT = data.temperature && data.temperature.length ? data.temperature[data.temperature.length - 1] : null;
    const lastP = data.pressure && data.pressure.length ? data.pressure[data.pressure.length - 1] : null;
    const lastPot = data.potential && data.potential.length ? data.potential[data.potential.length - 1] : null;
    const lastE = data.total_energy && data.total_energy.length ? data.total_energy[data.total_energy.length - 1] : null;

    document.getElementById("val-temperature").textContent = lastT !== null ? lastT.toFixed(1) + " K" : "-- K";
    document.getElementById("val-pressure").textContent = lastP !== null ? lastP.toFixed(0) + " bar" : "-- bar";
    document.getElementById("val-potential").textContent = lastPot !== null ? (lastPot / 1000).toFixed(1) + "×10³" : "--";
    document.getElementById("val-total-energy").textContent = lastE !== null ? (lastE / 1000).toFixed(1) + "×10³" : "--";

    // Performance: recent speed (rolling) and average speed (cumulative from first read)
    const recentEl = document.getElementById("stat-ns-per-day-recent");
    const avgEl = document.getElementById("stat-ns-per-day-avg");

    const recent = data.ns_per_day_recent;
    const cumul  = data.ns_per_day_cumulative;
    const finalV = data.ns_per_day_final;

    if (recentEl) {
        if (recent !== null && recent !== undefined) {
            recentEl.textContent = recent.toFixed(1) + " ns/day ⚡";
            recentEl.style.color = "var(--green)";
        } else {
            recentEl.textContent = "-- ns/day";
            recentEl.style.color = "var(--text-muted)";
        }
    }
    if (avgEl) {
        // Prefer live cumulative; fall back to final Performance block value
        const display = (cumul !== null && cumul !== undefined) ? cumul : finalV;
        if (display !== null && display !== undefined) {
            const suffix = (finalV !== null && finalV !== undefined && cumul === null) ? " ns/day ✓" : " ns/day";
            avgEl.textContent = display.toFixed(1) + suffix;
            avgEl.style.color = "var(--cyan)";
        } else {
            avgEl.textContent = "-- ns/day";
            avgEl.style.color = "var(--text-muted)";
        }
    }
    
    // Time format helper (seconds to HH:MM)
    const formatTime = (secs) => {
        if (!secs || secs <= 0) return "--";
        const h = Math.floor(secs / 3600);
        const m = Math.floor((secs % 3600) / 60);
        return `${h}h ${m}m`;
    };

    const stepTimeEl = document.getElementById("stat-step-time");
    if (stepTimeEl) {
        stepTimeEl.textContent = formatTime(data.step_wall_time_s);
    }
    
    const totalTimeEl = document.getElementById("stat-total-time");
    if (totalTimeEl) {
        totalTimeEl.textContent = formatTime(data.replica_wall_time_s);
    }

    const calendarTimeEl = document.getElementById("stat-calendar-time");
    if (calendarTimeEl) {
        calendarTimeEl.textContent = formatTime(data.replica_calendar_time_s);
    }

    const nPoints = data.temperature ? data.temperature.length : 0;
    document.getElementById("energy-badge").textContent = nPoints + " points";

    if (data.times) {
        if (miniChartTemp && data.temperature) {
            miniChartTemp.data.labels = data.times;
            miniChartTemp.data.datasets[0].data = data.temperature;
            miniChartTemp.update();
        }
        if (miniChartPres && data.pressure) {
            miniChartPres.data.labels = data.times;
            miniChartPres.data.datasets[0].data = data.pressure;
            miniChartPres.update();
        }
        if (miniChartPot && data.potential) {
            miniChartPot.data.labels = data.times;
            miniChartPot.data.datasets[0].data = data.potential;
            miniChartPot.update();
        }
        if (miniChartTotE && data.total_energy) {
            miniChartTotE.data.labels = data.times;
            miniChartTotE.data.datasets[0].data = data.total_energy;
            miniChartTotE.update();
        }
    }
}

// ── Charts ─────────────────────────────────────────────────────

function createMultiChart(canvasId, yLabel, configs) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: configs.map(c => ({
                label: c.label,
                data: [],
                borderColor: c.color,
                backgroundColor: c.color + "20",
                borderWidth: 1.5,
                pointRadius: 0,
                fill: configs.length === 1,
                tension: 0,
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: "Time (ps)", font: { size: 10 } },
                    ticks: { maxTicksLimit: 8, font: { size: 9 } },
                    grid: { color: "rgba(255,255,255,0.03)" }
                },
                y: {
                    title: { display: true, text: yLabel, font: { size: 10 } },
                    ticks: { maxTicksLimit: 6, font: { size: 9 } },
                    grid: { color: "rgba(255,255,255,0.03)" }
                }
            },
            plugins: {
                legend: { display: configs.length > 1, labels: { color: "#94a3b8", font: { size: 10 }, boxWidth: 12, padding: 8 } },
                tooltip: { mode: "index", intersect: false },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: "x",
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: "x",
                    }
                }
            },
            interaction: { mode: "nearest", axis: "x", intersect: false },
        }
    });
}

let miniChartTemp, miniChartPres, miniChartPot, miniChartTotE;

function createMiniChart(canvasId, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: color,
                borderWidth: 1.5,
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false }, zoom: { zoom: { wheel: { enabled: false } }, pan: { enabled: false } } },
            scales: {
                x: { display: false },
                y: { display: false, border: { display: false } }
            },
            layout: { padding: 0 }
        }
    });
}

function initCharts() {
    charts.rmsd = createMultiChart("chart-rmsd", "RMSD (Å)", [
        { label: "Complex", color: "#8b5cf6" },
        { label: "Chain A", color: "#3b82f6" },
        { label: "Chain B", color: "#ec4899" },
        { label: "Ligand", color: "#f59e0b" }
    ]);
    charts.rg = createMultiChart("chart-rg", "Rg (Å)", [
        { label: "Complex", color: CHART_COLORS.rg },
        { label: "Chain A", color: "#3b82f6" },
        { label: "Chain B", color: "#ec4899" }
    ]);
    charts.com = createMultiChart("chart-com", "Distance CoM (Å)", [
        { label: "Lig - Prot", color: "#10b981" },
        { label: "Lig - Chain A", color: "#3b82f6" },
        { label: "Lig - Chain B", color: "#ec4899" },
        { label: "Chain A - B", color: "#8b5cf6" }
    ]);
    charts.contacts = createMultiChart("chart-contacts", "Contacts (< 8Å)", [
        { label: "Lig - Prot", color: "#f59e0b" },
        { label: "Lig - Chain A", color: "#3b82f6" },
        { label: "Lig - Chain B", color: "#ec4899" },
        { label: "Chain A - B", color: "#8b5cf6" }
    ]);
    charts.temperature = createMultiChart("chart-temperature-main", "Temp (K)", [{ label: "Temperature", color: CHART_COLORS.temperature }]);

    miniChartTemp = createMiniChart("mini-chart-temperature", "#ef4444");
    miniChartPres = createMiniChart("mini-chart-pressure", "#3b82f6");
    miniChartPot = createMiniChart("mini-chart-potential", "#8b5cf6");
    miniChartTotE = createMiniChart("mini-chart-total-energy", "#f59e0b");
}

function initFullCharts() {
    if (Object.keys(chartsFull).length > 0) return; // already initialized
    chartsFull.rmsd = createMultiChart("chart-rmsd-full", "RMSD (Å)", [
        { label: "Complex", color: "#8b5cf6" },
        { label: "Chain A", color: "#3b82f6" },
        { label: "Chain B", color: "#ec4899" },
        { label: "Ligand", color: "#f59e0b" }
    ]);
    chartsFull.rg = createMultiChart("chart-rg-full", "Rg (Å)", [
        { label: "Complex", color: CHART_COLORS.rg },
        { label: "Chain A", color: "#3b82f6" },
        { label: "Chain B", color: "#ec4899" }
    ]);
    chartsFull.com = createMultiChart("chart-com-full", "Distance CoM (Å)", [
        { label: "Lig - Prot", color: "#10b981" },
        { label: "Lig - Chain A", color: "#3b82f6" },
        { label: "Lig - Chain B", color: "#ec4899" },
        { label: "Chain A - B", color: "#8b5cf6" }
    ]);
    chartsFull.contacts = createMultiChart("chart-contacts-full", "Contacts (< 5Å)", [
        { label: "Lig - Prot", color: "#f59e0b" },
        { label: "Lig - Chain A", color: "#3b82f6" },
        { label: "Lig - Chain B", color: "#ec4899" },
        { label: "Chain A - B", color: "#8b5cf6" }
    ]);
}

function destroyCharts() {
    Object.values(charts).forEach(c => { if (c) c.destroy(); });
    charts = {};
    if (miniChartTemp) { miniChartTemp.destroy(); miniChartTemp = null; }
    if (miniChartPres) { miniChartPres.destroy(); miniChartPres = null; }
    if (miniChartPot) { miniChartPot.destroy(); miniChartPot = null; }
    if (miniChartTotE) { miniChartTotE.destroy(); miniChartTotE = null; }
    
    // Clear Plotly Free Energy Landscape
    const felDiv = document.getElementById("chart-fel");
    if (felDiv) Plotly.purge(felDiv);
    const badge = document.getElementById("fel-badge");
    if (badge) badge.textContent = "--";
}

function destroyFullCharts() {
    Object.values(chartsFull).forEach(c => { if (c) c.destroy(); });
    chartsFull = {};
    
    // Clear Plotly Free Energy Landscape
    const felFullDiv = document.getElementById("chart-fel-full");
    if (felFullDiv) Plotly.purge(felFullDiv);
    const badge = document.getElementById("fel-badge-full");
    if (badge) badge.textContent = "--";
}

function updateMultiChart(chart, times, valuesArray, badge_id, unit, isGlobalView = false) {
    if (!chart || !times || !valuesArray || valuesArray.length === 0) return;

    // Downsample for performance if > 500 points
    let t = times;
    let vArrays = valuesArray;
    if (t.length > 500) {
        const step = Math.ceil(t.length / 500);
        t = t.filter((_, i) => i % step === 0);
        vArrays = valuesArray.map(arr => arr.filter((_, i) => i % step === 0));
    }

    chart.data.labels = t.map(x => x.toFixed(0));

    let stepAnnotations = {};
    
    if (isGlobalView) {
        let stepCount = 1;
        // Add S1 at the beginning
        stepAnnotations['step1'] = {
            type: 'line',
            xMin: 0,
            xMax: 0,
            borderColor: 'rgba(148, 163, 184, 0.6)',
            borderWidth: 1.5,
            borderDash: [4, 4],
            label: {
                display: true,
                content: 'S1',
                position: 'start',
                backgroundColor: 'rgba(30, 41, 59, 0.85)',
                color: '#e2e8f0',
                font: { size: 10, family: 'Inter' },
                padding: { x: 4, y: 2 }
            }
        };

        // The user requested adding S1, S2... when x is 0
        // S1 implicitly starts at the beginning, so we label subsequent steps when time hits 0
        for (let i = 1; i < t.length; i++) {
            // Also catch if time drops (e.g. restart without exactly 0)
            if (t[i] === 0 || t[i] < t[i-1]) {
                stepCount++;
                stepAnnotations['step' + stepCount] = {
                    type: 'line',
                    xMin: i,
                    xMax: i,
                    borderColor: 'rgba(148, 163, 184, 0.6)',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    label: {
                        display: true,
                        content: 'S' + stepCount,
                        position: 'start',
                        backgroundColor: 'rgba(30, 41, 59, 0.85)',
                        color: '#e2e8f0',
                        font: { size: 10, family: 'Inter' },
                        padding: { x: 4, y: 2 }
                    }
                };
            }
        }
    }
    
    if (isGlobalView) {
        if (!chart.options.plugins) chart.options.plugins = {};
        chart.options.plugins.annotation = {
            annotations: stepAnnotations
        };
    } else {
        if (chart.options.plugins && chart.options.plugins.annotation) {
            delete chart.options.plugins.annotation;
        }
    }

    for (let i = 0; i < vArrays.length; i++) {
        if (chart.data.datasets[i]) {
            chart.data.datasets[i].data = vArrays[i];
        }
    }
    chart.update("none");

    if (badge_id) {
        // Show value of the first dataset or complex
        const firstArr = vArrays[0];
        const last = firstArr && firstArr.length ? firstArr[firstArr.length - 1] : null;
        const el = document.getElementById(badge_id);
        if (el && last !== null) {
            el.textContent = (typeof last === "number" ? last.toFixed(1) : last) + (unit || "");
        }
    }
}

function updateTemperatureChart(data) {
    if (!data || !data.times || !data.temperature) return;
    updateMultiChart(charts.temperature, data.times, [data.temperature]);
}

function updateAnalysisCharts(data) {
    if (!data) return;
    updateMultiChart(charts.rmsd, data.times, [data.rmsd_complex, data.rmsd_chain_a, data.rmsd_chain_b, data.rmsd_ligand], "rmsd-badge", " Å");
    updateMultiChart(charts.rg, data.times, [data.rg, data.rg_chain_a, data.rg_chain_b], "rg-badge", " Å");
    updateMultiChart(charts.com, data.times, [data.com_lig_prot, data.com_lig_a, data.com_lig_b, data.com_a_b], "com-badge", " Å");
    updateMultiChart(charts.contacts, data.times, [data.cont_lig_prot, data.cont_lig_a, data.cont_lig_b, data.cont_a_b], "contacts-badge", "");
    if (data.fel) renderFELHeatmap(data.fel, "chart-fel", "fel-badge");
}

function updateFullAnalysisCharts(data) {
    if (!data) return;
    updateMultiChart(chartsFull.rmsd, data.times, [data.rmsd_complex, data.rmsd_chain_a, data.rmsd_chain_b, data.rmsd_ligand], "rmsd-badge-full", " Å", true);
    updateMultiChart(chartsFull.rg, data.times, [data.rg, data.rg_chain_a, data.rg_chain_b], "rg-badge-full", " Å", true);
    updateMultiChart(chartsFull.com, data.times, [data.com_lig_prot, data.com_lig_a, data.com_lig_b, data.com_a_b], "com-badge-full", " Å", true);
    updateMultiChart(chartsFull.contacts, data.times, [data.cont_lig_prot, data.cont_lig_a, data.cont_lig_b, data.cont_a_b], "contacts-badge-full", "", true);
    if (data.fel) renderFELHeatmap(data.fel, "chart-fel-full", "fel-badge-full");
}

// ── Free Energy Landscape Renderer ───────────────────────────

/**
 * Renders a 2D Boltzmann free energy landscape using Plotly.
 * @param {Object} fel  - Result of compute_fel_landscape() from backend
 * @param {string} divId - ID of the div container
 * @param {string} badgeId
 */
function renderFELHeatmap(fel, divId, badgeId) {
    const container = document.getElementById(divId);
    if (!container || !fel || !fel.energy) return;

    // ── Real-frame contour overlay (easy to toggle) ────────────
    // When true, draws a dotted white boundary around bins that contain
    // actual MD frames, distinguishing them from Gaussian-interpolated regions.
    // Set to false to hide the overlay entirely.
    const SHOW_REAL_CONTOURS = true;
    // ──────────────────────────────────────────────────────────

    const xmid = fel.xmid;   // RMSD axis
    const ymid = fel.ymid;   // Rg axis

    // null values arrive directly from Python (NaN → null in JSON).
    // The global minimum (ΔE=0.0) is a real float and renders correctly.
    const zData = fel.energy;

    const heatmapTrace = {
        z: zData,
        x: xmid,
        y: ymid,
        type: 'heatmap',
        colorscale: 'Viridis',
        reversescale: true,
        hoverongaps: false,
        hovertemplate: 'RMSD: %{x:.2f} Å<br>Rg: %{y:.2f} Å<br>ΔE: %{z:.2f} kcal/mol<extra></extra>',
        colorbar: {
            title: 'ΔE (kcal/mol)',
            titleside: 'right',
            tickfont: { color: '#94a3b8', size: 10 },
            titlefont: { color: '#94a3b8', size: 11 },
            thickness: 15,
            len: 0.8
        }
    };

    // Contour trace: boundary between real-frame bins (mask=1) and
    // Gaussian-interpolated bins (mask=0). Only the iso-line at 0.5 is drawn.
    const contourTrace = (SHOW_REAL_CONTOURS && fel.mask_real) ? {
        z: fel.mask_real,
        x: xmid,
        y: ymid,
        type: 'contour',
        showscale: false,
        contours: {
            coloring: 'none',    // no fill, only the line
            showlines: true,
            start: 0.5,
            end: 0.5,
            size: 1
        },
        line: {
            color: 'rgba(255, 255, 255, 0.55)',
            width: 1.5,
            dash: 'dot'
        },
        hoverinfo: 'skip',
        name: 'Real frames boundary'
    } : null;

    const minMarkerTrace = {
        x: [fel.min_rmsd],
        y: [fel.min_rg],
        mode: 'markers',
        type: 'scatter',
        name: 'Global Min',
        marker: {
            symbol: 'star',
            size: 14,
            color: '#ef4444',
            line: { color: 'rgba(255, 80, 80, 0.8)', width: 1 }
        },
        hovertemplate: 'Global Min<br>RMSD: %{x:.2f} Å<br>Rg: %{y:.2f} Å<extra></extra>'
    };

    const traces = [heatmapTrace];
    if (contourTrace) traces.push(contourTrace);
    traces.push(minMarkerTrace);

    const layout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        margin: { t: 10, r: 10, b: 40, l: 50 },
        xaxis: {
            title: { text: 'RMSD (Å)', font: { color: '#64748b', size: 11 } },
            tickfont: { color: '#94a3b8', size: 10 },
            gridcolor: 'rgba(255,255,255,0.03)',
            zeroline: false
        },
        yaxis: {
            title: { text: 'Rg (Å)', font: { color: '#64748b', size: 11 } },
            tickfont: { color: '#94a3b8', size: 10 },
            gridcolor: 'rgba(255,255,255,0.03)',
            zeroline: false
        },
        showlegend: false,
        autosize: true
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.react(divId, traces, layout, config);

    // ── Badge ──
    const badge = document.getElementById(badgeId);
    if (badge) badge.textContent = `${fel.n_frames} frames · min RMSD ${fel.min_rmsd.toFixed(2)} Å`;
}

// ── 3D Viewer ─────────────────────────────────────────────────

function loadPDB(url, animate = false) {
    const container = document.getElementById("mol-viewer");
    container.innerHTML = ""; // Clear placeholder

    fetch(url + "?t=" + Date.now())
        .then(r => r.text())
        .then(pdbData => {
            if (!pdbData || pdbData.length < 100) {
                container.innerHTML = '<div class="viewer-placeholder"><p>PDB data too small or empty</p></div>';
                return;
            }

            viewer3d = $3Dmol.createViewer(container, {
                backgroundColor: "#ffffff",
                antialias: true,
                orthographic: true,
                fog: false
            });

            if (animate) {
                viewer3d.addModelsAsFrames(pdbData, "pdb");
            } else {
                viewer3d.addModel(pdbData, "pdb");
            }

            // Estructura base en azul marino (ej: Cadena A o proteína genérica)
            viewer3d.setStyle({}, { cartoon: { color: "#1E3A8A", opacity: 1.0 } });

            // Cadena B en dorado
            viewer3d.setStyle({ chain: "B" }, { cartoon: { color: "#D4AF37", opacity: 1.0 } });

            // Ligando: stick
            viewer3d.setStyle(
                { resn: ["MOL", "LIG", "UNL"] },
                { stick: { colorscheme: "greenCarbon", radius: 0.2 }, sphere: { scale: 0.3, colorscheme: "greenCarbon" } }
            );

            viewer3d.zoomTo();
            viewer3d.zoom(0.8);
            viewer3d.render();

            if (animate) {
                viewer3d.animate({ loop: "forward", step: 1 });
                document.getElementById("viewer-badge").textContent = "Playing";
            } else {
                viewer3d.spin("y", 0.5);
                document.getElementById("viewer-badge").textContent = "Loaded";
            }
        })
        .catch(err => {
            container.innerHTML = `<div class="viewer-placeholder"><p>Error: ${err.message}</p></div>`;
        });
}

// ── Filter Buttons ────────────────────────────────────────────

document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter = btn.dataset.filter;
        renderSidebar();
    });
});

// ── Action Buttons ────────────────────────────────────────────

document.getElementById("back-btn").addEventListener("click", goBack);

document.getElementById("btn-refresh-analysis").addEventListener("click", () => {
    if (!selectedSystem || !selectedReplica) return;
    sendWS({ type: "get_analysis", system: selectedSystem, replica: selectedReplica });
    sendWS({ type: "get_log", system: selectedSystem, replica: selectedReplica });
});

document.getElementById("btn-refresh-pdb").addEventListener("click", () => {
    if (!selectedSystem || !selectedReplica) return;
    document.getElementById("mol-viewer").innerHTML = '<div class="viewer-placeholder"><p>Loading structure...</p></div>';
    document.getElementById("viewer-badge").textContent = "Loading...";
    if (viewer3d) { viewer3d.clear(); viewer3d = null; }
    sendWS({ type: "get_pdb", system: selectedSystem, replica: selectedReplica });
});

document.getElementById("btn-play-viewer").addEventListener("click", () => {
    if (!selectedSystem || !selectedReplica) return;
    document.getElementById("mol-viewer").innerHTML = '<div class="viewer-placeholder"><p>Extracting animation frames...</p></div>';
    document.getElementById("viewer-badge").textContent = "Extracting...";
    if (viewer3d) { viewer3d.clear(); viewer3d = null; }
    sendWS({ type: "get_trajectory_pdb", system: selectedSystem, replica: selectedReplica });
});

document.getElementById("btn-open-global").addEventListener("click", () => {
    if (!selectedSystem || !selectedReplica) return;
    document.getElementById("detail-view").classList.add("hidden");
    document.getElementById("full-traj-view").classList.remove("hidden");
    initFullCharts();
    sendWS({ type: "get_analysis_full", system: selectedSystem, replica: selectedReplica });
});

document.getElementById("back-btn-full").addEventListener("click", () => {
    document.getElementById("full-traj-view").classList.add("hidden");
    document.getElementById("detail-view").classList.remove("hidden");
});

document.getElementById("btn-refresh-full").addEventListener("click", () => {
    if (!selectedSystem || !selectedReplica) return;
    sendWS({ type: "get_analysis_full", system: selectedSystem, replica: selectedReplica });
});

document.getElementById("step-selector").addEventListener("change", (e) => {
    if (!selectedSystem || !selectedReplica) return;
    const step = e.target.value;
    if (step === "active") {
        sendWS({ type: "get_analysis", system: selectedSystem, replica: selectedReplica });
    } else {
        sendWS({ type: "get_analysis_step", system: selectedSystem, replica: selectedReplica, step: step });
    }
});

// ── Scan Timer ────────────────────────────────────────────────

setInterval(() => {
    scanCountdown--;
    if (scanCountdown <= 0) {
        scanCountdown = 60;
        sendWS({ type: "get_systems" });

        if (selectedSystem && selectedReplica) {
            const isFullView = !document.getElementById("full-traj-view").classList.contains("hidden");
            const stepVal = document.getElementById("step-selector").value;

            if (isFullView) {
                sendWS({ type: "get_analysis_full", system: selectedSystem, replica: selectedReplica });
            } else if (stepVal === "active") {
                sendWS({ type: "get_analysis", system: selectedSystem, replica: selectedReplica });
                sendWS({ type: "get_log", system: selectedSystem, replica: selectedReplica });
            }
        }
    }
    document.getElementById("scan-timer").textContent = `Next scan: ${scanCountdown}s`;
}, 1000);

// ── Init ──────────────────────────────────────────────────────

connectWS();
