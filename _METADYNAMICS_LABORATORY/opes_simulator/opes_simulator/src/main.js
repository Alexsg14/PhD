import Chart from 'chart.js/auto';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import { state, initSystem, simulationStep, N_BINS, MIN_X, MAX_X, DX } from './opes_engine.js';

Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.color = '#64748b';

const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    elements: {
        point: { radius: 0, hitRadius: 10, hoverRadius: 4 },
        line: { borderWidth: 2.5, tension: 0.2 }
    },
    plugins: {
        legend: {
            position: 'top',
            labels: { usePointStyle: true, boxWidth: 8, font: { weight: 500 } }
        },
        tooltip: { enabled: false }
    },
    scales: {
        x: {
            grid: { color: '#f1f5f9' },
            ticks: { maxTicksLimit: 8 }
        },
        y: {
            grid: { color: '#f1f5f9' }
        }
    }
};

let chartFES, chartBias, chartProb, chartTraj;
let animId;

function initCharts() {
    const ctxFES = document.getElementById('chartFES').getContext('2d');
    chartFES = new Chart(ctxFES, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'True FES', borderColor: '#94a3b8', data: [] },
                { label: 'OPES FES', borderColor: '#ef4444', borderDash: [5, 5], data: [] },
                { label: 'Particle', data: [], type: 'scatter', backgroundColor: '#3b82f6', pointRadius: 6, pointBorderColor: 'white', pointBorderWidth: 2 }
            ]
        },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { title: { display: true, text: 'Energy (kT)' } } } }
    });

    const ctxBias = document.getElementById('chartBias').getContext('2d');
    chartBias = new Chart(ctxBias, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Bias V(s)', borderColor: '#f59e0b', fill: true, backgroundColor: 'rgba(245, 158, 11, 0.1)', data: [] }] },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { title: { display: true, text: 'V(s)' } } } }
    });

    const ctxProb = document.getElementById('chartProb').getContext('2d');
    chartProb = new Chart(ctxProb, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Unbiased Prob (True)', borderColor: '#10b981', borderDash: [2, 2], data: [] }, { label: 'OPES Estimate', borderColor: '#8b5cf6', fill: true, backgroundColor: 'rgba(139, 92, 246, 0.1)', data: [] }] },
        options: { ...commonOptions, scales: { ...commonOptions.scales, y: { suggestedMin: 0, title: { display: true, text: 'Probability' } } } }
    });

    const ctxTraj = document.getElementById('chartTraj').getContext('2d');
    chartTraj = new Chart(ctxTraj, {
        type: 'bar',
        data: {
            labels: [], datasets: [
                { label: 'Target Prob', type: 'line', borderColor: '#eab308', borderDash: [2, 2], data: [], fill: false },
                { label: 'Instant Biased Prob', type: 'line', borderColor: '#06b6d4', data: [], fill: false, borderWidth: 1.5 },
                { label: 'Sampled Density', backgroundColor: '#cbd5e1', data: [], borderRadius: 4 }
            ]
        },
        options: { ...commonOptions }
    });
}

function updateChartsData() {
    let factor = 1 - 1 / state.GAMMA;
    let reconstructedFES = state.Bias.map(b => (b === 0 || factor === 0) ? null : -b / (factor * (1 / state.BETA)));

    let p_idx = Math.max(0, Math.min(N_BINS - 1, Math.floor((state.current_x - MIN_X) / DX)));
    let particleData = new Array(N_BINS).fill(null);
    if (state.current_x >= MIN_X && state.current_x <= MAX_X) {
        particleData[p_idx] = state.FES_true[p_idx];
    }

    chartFES.data.labels = state.x_space;
    chartFES.data.datasets[0].data = state.FES_true;
    chartFES.data.datasets[1].data = reconstructedFES;
    chartFES.data.datasets[2].data = particleData;
    chartFES.update();

    chartBias.data.labels = state.x_space;
    chartBias.data.datasets[0].data = state.Bias;
    chartBias.update();

    chartProb.data.labels = state.x_space;
    chartProb.data.datasets[0].data = state.Prob_unbiased;
    chartProb.data.datasets[1].data = state.Prob_est;
    chartProb.update();

    let Prob_biased_inst = new Array(N_BINS).fill(0);
    let Z_biased = 0;
    for (let i = 0; i < N_BINS; i++) {
        let e_biased = state.FES_true[i] + state.Bias[i];
        let p_b = Math.exp(-state.BETA * e_biased);
        Prob_biased_inst[i] = p_b;
        Z_biased += p_b * DX;
    }
    for (let i = 0; i < N_BINS; i++) {
        Prob_biased_inst[i] /= (Z_biased > 0 ? Z_biased : 1);
    }

    let sum_hist = state.Histogram.reduce((a, b) => a + b, 0);
    let Hist_norm = state.Histogram.map(h => sum_hist > 0 ? h / (sum_hist * DX) : 0);

    chartTraj.data.labels = state.x_space;
    chartTraj.data.datasets[0].data = state.Prob_target;
    chartTraj.data.datasets[1].data = Prob_biased_inst;
    chartTraj.data.datasets[2].data = Hist_norm;
    chartTraj.update();
}

function readUIParams() {
    return {
        gamma: parseFloat(document.getElementById('input-gamma').value),
        beta: parseFloat(document.getElementById('input-beta').value),
        barrier: parseFloat(document.getElementById('input-barrier').value),
        speed: parseInt(document.getElementById('input-speed').value, 10),
        equation: document.getElementById('input-equation').value
    };
}

function renderMath() {
    const eq1 = `V(\\xi) = -\\frac{1}{\\beta} \\ln \\frac{p^{tg}(\\xi)}{P(\\xi)}`;
    const proofStr = `\\int \\delta[\\xi'(r) - \\xi] e^{-\\beta(E+V)} d^N r = \\frac{p^{tg}(\\xi)}{P(\\xi)} \\int \\delta[\\xi'(r) - \\xi] e^{-\\beta E} d^N r \\propto p^{tg}(\\xi)`;
    const eq2 = `p^{tg} = [P(\\xi)]^{1/\\gamma}`;
    const eq3 = `P_n(\\xi) = \\frac{\\sum_k^n w_k G(\\xi(t), \\xi(t'))}{\\sum_k^n w_k} \\quad \\text{where} \\quad w_k = e^{\\beta V_{k-1}(\\xi)}`;
    const eq4 = `V_n(\\xi) = -\\frac{1}{\\beta} \\ln \\frac{p^{tg}(\\xi)}{P_n(\\xi)} = \\left(1 - \\frac{1}{\\gamma}\\right)\\frac{1}{\\beta}\\ln\\left(\\frac{P_n(\\xi)}{Z_n} + \\epsilon\\right)`;
    const znCode = `Z_n = \\sum_k e^{\\beta V_{k-1}(\\xi_k)}`;
    const epsCode = `\\epsilon = e^{-\\frac{\\beta \\Delta E}{1 - 1/\\gamma}}`;

    katex.render(eq1, document.getElementById('katex-eq1'), { throwOnError: false, displayMode: true });
    katex.render(proofStr, document.getElementById('katex-proof'), { throwOnError: false, displayMode: true });
    katex.render(eq2, document.getElementById('katex-eq2'), { throwOnError: false, displayMode: true });
    katex.render(eq3, document.getElementById('katex-eq3'), { throwOnError: false, displayMode: true });
    katex.render(eq4, document.getElementById('katex-eq4'), { throwOnError: false, displayMode: true });
    katex.render(znCode, document.getElementById('katex-zn'), { throwOnError: false, displayMode: false });
    katex.render(epsCode, document.getElementById('katex-eps-code'), { throwOnError: false, displayMode: false });
}

function handleReset() {
    const p = readUIParams();
    initSystem(p.gamma, p.beta, p.barrier, p.speed, p.equation);
    document.getElementById('equation-error').innerText = state.lastError;
    updateChartsData();
}

function setupControls() {
    const controls = ['gamma', 'beta', 'barrier', 'speed'];
    controls.forEach(c => {
        const slider = document.getElementById(`slider-${c}`);
        const input = document.getElementById(`input-${c}`);

        slider.addEventListener('input', (e) => {
            input.value = e.target.value;
            if (c === 'speed') state.STEPS_PER_FRAME = parseInt(e.target.value, 10);
            else if (!state.isRunning) handleReset();
        });

        input.addEventListener('input', (e) => {
            slider.value = e.target.value;
            if (c === 'speed') state.STEPS_PER_FRAME = parseInt(e.target.value, 10);
            else if (!state.isRunning) handleReset();
        });
    });

    document.getElementById('input-equation').addEventListener('change', () => {
        if (!state.isRunning) handleReset();
    });

    const btnToggle = document.getElementById('btn-toggle');
    btnToggle.addEventListener('click', toggleSimulation);

    document.getElementById('btn-reset').addEventListener('click', handleReset);
    
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
            e.preventDefault();
            toggleSimulation();
        }
    });
}

function toggleSimulation() {
    state.isRunning = !state.isRunning;
    const btn = document.getElementById('btn-toggle');
    if (state.isRunning) {
        btn.classList.add('paused');
        btn.innerHTML = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> <span>Pause Simulation</span>`;
        frame();
    } else {
        btn.classList.remove('paused');
        btn.innerHTML = `<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> <span>Start Simulation</span>`;
        cancelAnimationFrame(animId);
    }
}

function frame() {
    if (!state.isRunning) return;
    simulationStep();
    updateChartsData();
    animId = requestAnimationFrame(frame);
}

function setupTabs() {
    const tabSim = document.getElementById('tab-sim');
    const tabTheory = document.getElementById('tab-theory');
    const viewSim = document.getElementById('view-sim');
    const viewTheory = document.getElementById('view-theory');

    tabSim.addEventListener('click', () => {
        tabSim.classList.add('active');
        tabTheory.classList.remove('active');
        viewSim.style.display = 'block';
        viewTheory.style.display = 'none';
    });

    tabTheory.addEventListener('click', () => {
        tabTheory.classList.add('active');
        tabSim.classList.remove('active');
        viewTheory.style.display = 'block';
        viewSim.style.display = 'none';
    });
}

renderMath();
setupTabs();
initCharts();
setupControls();
handleReset();
