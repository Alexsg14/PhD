import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MathBlock } from './MathEq';
import OpesVisualizer from './OpesVisualizer';
import {
  Play, Pause, RotateCcw, Activity, BookOpen, Zap, Sliders, AlertCircle, Upload
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Bar, ComposedChart, Area
} from 'recharts';

// ─────────────────────────────────────────────────────────────
// OPES ENGINE — pure JS, no external deps
// ─────────────────────────────────────────────────────────────
const N_BINS = 100;
const MIN_X  = -2.5;
const MAX_X  =  2.5;
const DX     = (MAX_X - MIN_X) / N_BINS;

function buildXSpace() {
  return Array.from({ length: N_BINS }, (_, i) => parseFloat((MIN_X + i * DX).toFixed(3)));
}

// ── Safe math parser (same pattern as MetadynamicsLab) ─────────
const parseAndEvalMath = (expr, x) => {
  if (!expr || typeof expr !== 'string') return 0;
  try {
    let str = expr.toLowerCase().trim();
    if (!str) return 0;
    str = str.replace(/(\d)\s*([a-z(])/g, '$1*$2');
    str = str.replace(/(\))\s*([a-z0-9(])/g, '$1*$2');
    const tokens = [];
    let i = 0;
    while (i < str.length) {
      const ch = str[i];
      if (/\s/.test(ch)) { i++; continue; }
      if (/[0-9.]/.test(ch)) {
        let numStr = '';
        while (i < str.length && /[0-9.]/.test(str[i])) { numStr += str[i]; i++; }
        tokens.push({ type: 'NUM', val: parseFloat(numStr) });
        continue;
      }
      if (/[a-z]/.test(ch)) {
        let idStr = '';
        while (i < str.length && /[a-z0-9_]/.test(str[i])) { idStr += str[i]; i++; }
        tokens.push({ type: 'ID', val: idStr });
        continue;
      }
      if ('+-*/^()'.includes(ch)) { tokens.push({ type: 'OP', val: ch }); i++; continue; }
      return NaN;
    }
    let pos = 0;
    const peek = () => tokens[pos] || null;
    const consume = () => tokens[pos++] || null;
    const parseExpr = () => parseAddSub();
    const parseAddSub = () => {
      let left = parseMulDiv();
      while (peek() && peek().type === 'OP' && (peek().val === '+' || peek().val === '-')) {
        const op = consume().val;
        const right = parseMulDiv();
        left = op === '+' ? left + right : left - right;
      }
      return left;
    };
    const parseMulDiv = () => {
      let left = parsePow();
      while (peek() && peek().type === 'OP' && (peek().val === '*' || peek().val === '/')) {
        const op = consume().val;
        const right = parsePow();
        left = op === '*' ? left * right : left / right;
      }
      return left;
    };
    const parsePow = () => {
      let base = parseUnary();
      if (peek() && peek().type === 'OP' && peek().val === '^') {
        consume();
        const exp = parseUnary();
        base = Math.pow(base, exp);
      }
      return base;
    };
    const parseUnary = () => {
      if (peek() && peek().type === 'OP' && peek().val === '-') { consume(); return -parseAtom(); }
      if (peek() && peek().type === 'OP' && peek().val === '+') { consume(); return parseAtom(); }
      return parseAtom();
    };
    const parseAtom = () => {
      const tok = peek();
      if (!tok) return 0;
      if (tok.type === 'NUM') { consume(); return tok.val; }
      if (tok.type === 'ID') {
        consume();
        if (tok.val === 'x') return x;
        if (tok.val === 'pi') return Math.PI;
        if (tok.val === 'e') return Math.E;
        const fnMap = { sin: Math.sin, cos: Math.cos, tan: Math.tan, exp: Math.exp, log: Math.log, sqrt: Math.sqrt, abs: Math.abs, asin: Math.asin, acos: Math.acos, atan: Math.atan };
        if (fnMap[tok.val] && peek() && peek().val === '(') {
          consume();
          const arg = parseExpr();
          if (peek() && peek().val === ')') consume();
          return fnMap[tok.val](arg);
        }
        return 0;
      }
      if (tok.type === 'OP' && tok.val === '(') {
        consume();
        const val = parseExpr();
        if (peek() && peek().val === ')') consume();
        return val;
      }
      return 0;
    };
    const result = parseExpr();
    return isFinite(result) ? result : NaN;
  } catch {
    return NaN;
  }
};

function buildSystem(gamma, beta, barrier, equationStr) {
  const xSpace = buildXSpace();
  const factor = 1.0 - 1.0 / gamma;
  const epsilon = Math.exp((-beta * barrier) / factor);
  const normFactor = Math.pow(epsilon, factor);

  const FES_true = xSpace.map(x => {
    const v = parseAndEvalMath(equationStr, x);
    return isNaN(v) ? 0 : v;
  });

  let Z_target = 0, Z_unbiased = 0;
  const Prob_target   = FES_true.map(e => { const p = Math.exp(-beta * e / gamma); Z_target   += p * DX; return p; });
  const Prob_unbiased = FES_true.map(e => { const p = Math.exp(-beta * e);          Z_unbiased += p * DX; return p; });
  Prob_target.forEach((_, i)   => { Prob_target[i]   /= Z_target   || 1; });
  Prob_unbiased.forEach((_, i) => { Prob_unbiased[i] /= Z_unbiased || 1; });

  return { xSpace, FES_true, Prob_target, Prob_unbiased, epsilon, normFactor };
}

function createSimState(gamma, beta, barrier, equationStr, speed) {
  const sys = buildSystem(gamma, beta, barrier, equationStr);
  const factor = 1.0 - 1.0 / gamma;
  return {
    ...sys,
    gamma, beta, barrier, equationStr, speed,
    factor,
    epsilon: sys.epsilon,
    normFactor: sys.normFactor,
    Bias:            new Float64Array(N_BINS),
    Histogram:       new Float64Array(N_BINS),
    Prob_est:        new Float64Array(N_BINS),
    weighted_counts: new Float64Array(N_BINS),
    sum_weights:  sys.normFactor,
    sum_weights2: sys.normFactor * sys.normFactor,
    sigma_0: 0.2,
    current_x: -1.0,
    stepCount: 0,
  };
}

function stepSimulation(state, nSteps) {
  const { FES_true, Bias, Histogram, weighted_counts, beta, sigma_0, factor, epsilon } = state;
  let { current_x, sum_weights, sum_weights2, stepCount } = state;

  for (let step = 0; step < nSteps; step++) {
    const dx  = (Math.random() - 0.5) * 0.8;
    let x_new = current_x + dx;
    if (x_new < MIN_X)  x_new = MIN_X + 0.01;
    if (x_new >= MAX_X) x_new = MAX_X - 0.01;

    const idx_curr = Math.max(0, Math.min(N_BINS - 1, Math.floor((current_x - MIN_X) / DX)));
    const idx_new  = Math.max(0, Math.min(N_BINS - 1, Math.floor((x_new  - MIN_X) / DX)));

    if (Math.exp(-beta * ((FES_true[idx_new] + Bias[idx_new]) - (FES_true[idx_curr] + Bias[idx_curr]))) > Math.random()) {
      current_x = x_new;
    }

    const idx_acc = Math.max(0, Math.min(N_BINS - 1, Math.floor((current_x - MIN_X) / DX)));
    Histogram[idx_acc]++;

    if (step % 5 === 0) {
      const w = Math.exp(beta * Bias[idx_acc]);
      weighted_counts[idx_acc] += w;
      sum_weights  += w;
      sum_weights2 += w * w;
    }
    stepCount++;
  }

  // Update OPES bias (KDE) — band-limited: only visit bins within ~5σ
  if (sum_weights > 0) {
    const n_eff = Math.pow(1.0 + sum_weights, 2) / (1.0 + sum_weights2);
    let sigma_i = sigma_0 * Math.pow((n_eff * 3.0 / 4.0), -0.2);
    sigma_i = Math.max(sigma_i, DX * 0.8);
    const inv_s2  = 1.0 / (sigma_i * sigma_i);
    const bw_bins = Math.ceil(Math.sqrt(24) * sigma_i / DX) + 1; // cutoff at ~5σ
    const prob_unnorm = new Float64Array(N_BINS);
    let Z_n = 0;
    for (let i = 0; i < N_BINS; i++) {
      let p_x = 0;
      const j0 = Math.max(0, i - bw_bins);
      const j1 = Math.min(N_BINS - 1, i + bw_bins);
      for (let j = j0; j <= j1; j++) {
        if (weighted_counts[j] > 0) {
          const dist = (i - j) * DX;
          p_x += weighted_counts[j] * Math.exp(-0.5 * dist * dist * inv_s2);
        }
      }
      prob_unnorm[i] = p_x / sum_weights;
      Z_n += prob_unnorm[i] * DX;
    }
    for (let i = 0; i < N_BINS; i++) {
      const p_norm = prob_unnorm[i] / (Z_n > 0 ? Z_n : 1);
      state.Prob_est[i] = p_norm;
      state.Bias[i]     = factor * (1.0 / beta) * Math.log(p_norm + epsilon);
    }
  }

  state.current_x   = current_x;
  state.sum_weights  = sum_weights;
  state.sum_weights2 = sum_weights2;
  state.stepCount    = stepCount;
}

// ─────────────────────────────────────────────────────────────
// CHART CONFIG
// ─────────────────────────────────────────────────────────────
const CC = {
  trueFes: '#94a3b8', opesFes: '#f87171', particle: '#38bdf8',
  bias: '#fbbf24', probTrue: '#34d399', probOpes: '#a78bfa',
  target: '#facc15', biasedP: '#22d3ee',
};
const TT  = { backgroundColor: 'rgba(15,23,42,0.95)', border: '1px solid rgba(51,65,85,0.8)', borderRadius: '8px', fontSize: '11px', color: '#cbd5e1' };
const AX  = { fill: '#64748b', fontSize: 10 };
const CG  = { strokeDasharray: '3 3', stroke: 'rgba(51,65,85,0.4)' };
const MAR = { top: 5, right: 10, left: -10, bottom: 0 };

// ─────────────────────────────────────────────────────────────
// OPES SIMULATOR COMPONENT
// ─────────────────────────────────────────────────────────────
const DEFAULT_EQ = '2.0 * (x^4 - 4*x^2 + 0.5*x) + 10.0';
const PRESETS = [
  { label: 'Asymmetric Double Well', expr: '2.0 * (x^4 - 4*x^2 + 0.5*x) + 10.0' },
  { label: 'Symmetric Double Well',  expr: '(x^2 - 4)^2 + 5' },
  { label: 'Triple Well',            expr: '(x^2 - 4)^2 * (x^2 - 1) + 8' },
  { label: 'Harmonic',               expr: '2 * x^2' },
  { label: 'Sinusoidal',             expr: '3 * cos(2 * x) + 0.15 * x^4 + 5' },
];

export default function OPESSimulator() {
  const [gamma,    setGamma]    = useState(5.0);
  const [beta,     setBeta]     = useState(1.0);
  const [barrier,  setBarrier]  = useState(15.0);
  const [speed,    setSpeed]    = useState(50);
  const [equation, setEquation] = useState(DEFAULT_EQ);
  const [eqDraft,  setEqDraft]  = useState(DEFAULT_EQ);
  const [eqError,  setEqError]  = useState('');
  const [activeTab, setActiveTab] = useState('sim');

  const simRef  = useRef(null);
  const rafRef  = useRef(null);
  const [running,   setRunning]   = useState(false);
  const [chartData, setChartData] = useState(null);
  const [stepCount, setStepCount] = useState(0);

  // Initialize simulation state
  const initSim = useCallback((g, b, bar, eq, spd) => {
    const test = parseAndEvalMath(eq, 0);
    if (isNaN(test)) { setEqError('Invalid equation.'); return false; }
    setEqError('');
    simRef.current = createSimState(g, b, bar, eq, spd);
    return true;
  }, []);

  // Build chart snapshot — single pass, Float64Array, no Array.from
  const buildChartData = useCallback(() => {
    const s = simRef.current;
    if (!s) return;
    const factor  = 1 - 1 / s.gamma;
    const invBeta = 1 / s.beta;

    let sumHist = 0;
    for (let i = 0; i < N_BINS; i++) sumHist += s.Histogram[i];

    let Z_biased = 0;
    const PBI = new Float64Array(N_BINS);
    for (let i = 0; i < N_BINS; i++) {
      const p = Math.exp(-s.beta * (s.FES_true[i] + s.Bias[i]));
      PBI[i] = p;
      Z_biased += p * DX;
    }
    if (Z_biased > 0) for (let i = 0; i < N_BINS; i++) PBI[i] /= Z_biased;

    const p_idx = Math.max(0, Math.min(N_BINS - 1, Math.floor((s.current_x - MIN_X) / DX)));
    const fes  = new Array(N_BINS);
    const bias = new Array(N_BINS);
    const prob = new Array(N_BINS);
    const traj = new Array(N_BINS);

    for (let i = 0; i < N_BINS; i++) {
      const x = s.xSpace[i];
      const opesFes = (factor !== 0 && s.Bias[i] !== 0)
        ? +(-s.Bias[i] / (factor * invBeta)).toFixed(4)
        : null;
      fes[i]  = { x, trueFes: +s.FES_true[i].toFixed(4), opesFes, particle: i === p_idx ? +s.FES_true[i].toFixed(4) : null };
      bias[i] = { x, bias: +s.Bias[i].toFixed(4) };
      prob[i] = { x, probTrue: +s.Prob_unbiased[i].toFixed(6), probOpes: +s.Prob_est[i].toFixed(6) };
      traj[i] = { x, target: +s.Prob_target[i].toFixed(6), biasedP: +PBI[i].toFixed(6), hist: sumHist > 0 ? +(s.Histogram[i] / (sumHist * DX)).toFixed(6) : 0 };
    }

    setChartData({ fes, bias, prob, traj });
    setStepCount(s.stepCount);
  }, []);

  useEffect(() => { initSim(gamma, beta, barrier, equation, speed); buildChartData(); }, []); // eslint-disable-line

  // RAF loop: simulation at ~20fps, charts at ~10fps (prevents setInterval queue buildup)
  useEffect(() => {
    if (!running) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      return;
    }
    const SIM_MS   = 50; // step simulation every ~50ms
    const CHART_MS = 50;  // rebuild charts every ~50ms (~20fps, same as MetadynamicsLab)
    let lastSim   = 0;
    let lastChart = 0;

    const tick = (now) => {
      if (now - lastSim >= SIM_MS && simRef.current) {
        stepSimulation(simRef.current, simRef.current.speed);
        lastSim = now;
        if (now - lastChart >= CHART_MS) {
          buildChartData();
          lastChart = now;
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [running, buildChartData]);

  const startSim  = useCallback(() => { setRunning(true); }, []);
  const pauseSim  = useCallback(() => { setRunning(false); }, []);
  const toggleSim = useCallback(() => { setRunning((prev) => !prev); }, []);

  const handleReset = useCallback(() => {
    setRunning(false);
    if (initSim(gamma, beta, barrier, equation, speed)) buildChartData();
  }, [gamma, beta, barrier, equation, speed, initSim, buildChartData]);

  useEffect(() => { if (simRef.current) simRef.current.speed = speed; }, [speed]);

  const applyEquation = useCallback(() => {
    if (isNaN(parseAndEvalMath(eqDraft, 0))) { setEqError('Ecuación inválida. Usa x como variable.'); return; }
    setEqError('');
    setEquation(eqDraft);
    cancelAnimationFrame(rafRef.current);
    setRunning(false);
    if (initSim(gamma, beta, barrier, eqDraft, speed)) buildChartData();
  }, [eqDraft, gamma, beta, barrier, speed, initSim, buildChartData]);

  useEffect(() => () => cancelAnimationFrame(rafRef.current), []);

  const SLIDERS = [
    { label: 'Bias Factor (γ)',     id: 'gamma',   val: gamma,   set: setGamma,   min: 1.1, max: 100, step: 0.1, color: 'cyan',    unit: '',             desc: 'Flatter target distribution' },
    { label: 'Inverse Temp (β)',    id: 'beta',    val: beta,    set: setBeta,    min: 0.1, max: 5,   step: 0.1, color: 'indigo',  unit: '',             desc: 'Inverse temperature of the system' },
    { label: 'Energy Barrier (ΔE)', id: 'barrier', val: barrier, set: setBarrier, min: 1,   max: 40,  step: 1,   color: 'emerald', unit: 'kT',           desc: 'Regulates regularization parameter ε' },
    { label: 'Sim Speed',           id: 'speed',   val: speed,   set: setSpeed,   min: 1,   max: 300, step: 5,   color: 'amber',   unit: 'steps/frame',  desc: 'Steps per animation frame' },
  ];

  return (
    <div className="space-y-3">

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg shadow-amber-500/20 text-white">
            <Zap size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">OPES 1D Simulator</h2>
            <p className="text-[11px] text-amber-400 font-mono tracking-wide">On-the-fly Probability Enhanced Sampling</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex bg-slate-900/80 border border-slate-800 rounded-xl p-1 gap-1">
            <button onClick={() => setActiveTab('sim')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${activeTab === 'sim' ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}>
              Simulation
            </button>
            <button onClick={() => setActiveTab('theory')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${activeTab === 'theory' ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md' : 'text-slate-400 hover:text-slate-200'}`}>
              <BookOpen size={12} /> Theory
            </button>
          </div>
          <button onClick={toggleSim}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-md ${running ? 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white shadow-amber-500/20' : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/20'}`}>
            {running ? <><Pause size={14} /> Pause</> : <><Play size={14} /> Start</>}
          </button>
          <button onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-xl text-xs font-bold transition-all">
            <RotateCcw size={14} /> Reset
          </button>
        </div>
      </div>

      {/* Status badges */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
          <Activity size={12} className="text-amber-400" />
          <span className="text-[10px] font-mono text-white">Steps:</span>
          <span className="text-[11px] font-bold font-mono text-amber-300">{stepCount.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 bg-slate-900/80 border border-slate-800 rounded-lg">
          <span className="text-[10px] font-mono text-white">γ =</span>
          <span className="text-[11px] font-bold font-mono text-cyan-300">{gamma}</span>
          <span className="text-[10px] font-mono text-slate-500 mx-0.5">|</span>
          <span className="text-[10px] font-mono text-white">β =</span>
          <span className="text-[11px] font-bold font-mono text-indigo-300">{beta}</span>
          <span className="text-[10px] font-mono text-slate-500 mx-0.5">|</span>
          <span className="text-[10px] font-mono text-white">ΔE =</span>
          <span className="text-[11px] font-bold font-mono text-emerald-300">{barrier} kT</span>
        </div>
      </div>

      {/* SIMULATION TAB */}
      {activeTab === 'sim' && (
        <>
          {/* Controls panel */}
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl">
            <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-1.5 mb-2.5">
              <Sliders size={13} className="text-amber-400" /> Simulation Parameters
            </h3>

            {/* Equation input */}
            <div className="mb-3">
              <label className="block text-[11px] text-white mb-1 font-semibold">True Energy Surface E(x)</label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type="text" value={eqDraft} spellCheck={false}
                    onChange={e => setEqDraft(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && applyEquation()}
                    className={`w-full bg-slate-950 border rounded-xl px-2.5 py-1 text-xs text-amber-300 font-mono outline-none transition-all ${eqError ? 'border-red-500/60' : 'border-slate-700 focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/50'}`}
                    placeholder="e.g. x^4 - 4*x^2 + 0.5*x"
                  />
                  {eqError && (
                    <div className="flex items-center gap-1 mt-0.5 text-[10px] text-red-400">
                      <AlertCircle size={10} /> {eqError}
                    </div>
                  )}
                </div>
                <button onClick={applyEquation}
                  className="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold transition-all self-start">
                  Apply
                </button>
              </div>
              <div className="flex flex-wrap gap-1 mt-1.5">
                {PRESETS.map(p => (
                  <button key={p.label} onClick={() => { setEqDraft(p.expr); setEqError(''); }}
                    className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-amber-500/40 text-white hover:text-amber-300 rounded-lg text-[10px] font-mono transition-all">
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Parameter sliders */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {SLIDERS.map(({ label, id, val, set, min, max, step, color, unit, desc }) => (
                <div key={id} className="space-y-1">
                  <div className="flex justify-between items-center gap-2">
                    <label className="text-[11px] font-semibold text-white truncate">{label}</label>
                    <div className="flex items-center gap-1 px-1.5 py-0.5 bg-slate-950 border border-slate-700 rounded-lg shrink-0">
                      <input
                        type="number" value={val} min={min} max={max} step={step}
                        onChange={e => set(parseFloat(e.target.value) || val)}
                        className={`w-12 bg-transparent text-xs font-bold font-mono outline-none text-right text-${color}-300`}
                      />
                    </div>
                  </div>
                  <input type="range" min={min} max={max} step={step} value={val}
                    onChange={e => set(parseFloat(e.target.value))}
                    className="w-full h-1.5 appearance-none bg-slate-800 rounded-full outline-none cursor-pointer"
                    style={{ accentColor: color === 'cyan' ? '#22d3ee' : color === 'indigo' ? '#818cf8' : color === 'emerald' ? '#34d399' : '#fbbf24' }}
                  />
                  <p className="text-[9px] text-slate-400 font-mono">{desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Charts 2x2 grid */}
          {chartData && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">

              {/* FES */}
              <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl">
                <h3 className="text-xs font-bold text-white mb-0.5">Free Energy Surface (FES)</h3>
                <p className="text-[10px] text-slate-400 mb-1.5 font-mono">True FES vs OPES reconstruction · particle position</p>
                <ResponsiveContainer width="100%" height={210}>
                  <LineChart data={chartData.fes} margin={MAR}>
                    <CartesianGrid {...CG} />
                    <XAxis dataKey="x" tick={AX} />
                    <YAxis tick={AX} label={{ value: 'E (kT)', angle: -90, position: 'insideLeft', offset: 15, fill: '#64748b', fontSize: 10 }} />
                    <Tooltip contentStyle={TT} formatter={v => v?.toFixed(3)} />
                    <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
                    <Line type="monotone" dataKey="trueFes"  name="True FES"  stroke={CC.trueFes}  dot={false} strokeWidth={2} isAnimationActive={false} />
                    <Line type="monotone" dataKey="opesFes"  name="OPES FES"  stroke={CC.opesFes}  dot={false} strokeWidth={2} strokeDasharray="5 4" connectNulls={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="particle" name="Particle"   stroke={CC.particle} dot={{ r: 5, fill: CC.particle, strokeWidth: 2, stroke: '#0f172a' }} connectNulls={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Bias */}
              <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl">
                <h3 className="text-xs font-bold text-white mb-0.5">Accumulated Bias V(s)</h3>
                <p className="text-[10px] text-slate-400 mb-1.5 font-mono">Potencial de sesgo acumulado on-the-fly</p>
                <ResponsiveContainer width="100%" height={210}>
                  <ComposedChart data={chartData.bias} margin={MAR}>
                    <CartesianGrid {...CG} />
                    <XAxis dataKey="x" tick={AX} />
                    <YAxis tick={AX} label={{ value: 'V(s)', angle: -90, position: 'insideLeft', offset: 15, fill: '#64748b', fontSize: 10 }} />
                    <Tooltip contentStyle={TT} formatter={v => v?.toFixed(4)} />
                    <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
                    <Area type="monotone" dataKey="bias" name="Bias V(s)" stroke={CC.bias} fill="rgba(251,191,36,0.12)" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* Probability */}
              <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl">
                <h3 className="text-xs font-bold text-white mb-0.5">Probability Distribution P(ξ)</h3>
                <p className="text-[10px] text-slate-400 mb-1.5 font-mono">Unbiased true P(ξ) vs OPES on-the-fly estimate</p>
                <ResponsiveContainer width="100%" height={210}>
                  <LineChart data={chartData.prob} margin={MAR}>
                    <CartesianGrid {...CG} />
                    <XAxis dataKey="x" tick={AX} />
                    <YAxis tick={AX} label={{ value: 'P(ξ)', angle: -90, position: 'insideLeft', offset: 15, fill: '#64748b', fontSize: 10 }} />
                    <Tooltip contentStyle={TT} formatter={v => v?.toFixed(5)} />
                    <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
                    <Line type="monotone" dataKey="probTrue" name="True P(ξ)"     stroke={CC.probTrue} dot={false} strokeWidth={2} strokeDasharray="4 3" isAnimationActive={false} />
                    <Line type="monotone" dataKey="probOpes" name="OPES Estimate"  stroke={CC.probOpes} dot={false} strokeWidth={2} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Trajectory */}
              <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl">
                <h3 className="text-xs font-bold text-white mb-0.5">Trajectory & Sampling Density</h3>
                <p className="text-[10px] text-slate-400 mb-1.5 font-mono">Target · inst. biased prob · sampled histogram</p>
                <ResponsiveContainer width="100%" height={210}>
                  <ComposedChart data={chartData.traj} margin={MAR}>
                    <CartesianGrid {...CG} />
                    <XAxis dataKey="x" tick={AX} />
                    <YAxis tick={AX} />
                    <Tooltip contentStyle={TT} formatter={v => v?.toFixed(5)} />
                    <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
                    <Bar dataKey="hist"    name="Sampled Density"    fill="rgba(71,85,105,0.5)" radius={[2,2,0,0]} isAnimationActive={false} />
                    <Line type="monotone" dataKey="target"  name="Target p^tg"     stroke={CC.target}  dot={false} strokeWidth={1.5} strokeDasharray="4 3" isAnimationActive={false} />
                    <Line type="monotone" dataKey="biasedP" name="Inst. Biased P"  stroke={CC.biasedP} dot={false} strokeWidth={1.5} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

            </div>
          )}
        </>
      )}

      {/* THEORY TAB */}
      {activeTab === 'theory' && (
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <h2 className="text-base font-bold text-white border-b border-slate-800 pb-3">
            On-the-fly Probability Enhanced Sampling (OPES)
          </h2>
          <div className="space-y-4 text-sm text-slate-400 leading-relaxed">
            <p>A new expression for the bias potential is introduced:</p>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <MathBlock tex={`V(\\xi) = -\\frac{1}{\\beta} \\ln \\frac{p^{\\rm tg}(\\xi)}{P(\\xi)}`} />
            </div>
            <p>Such that the biased probability matches the target:</p>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <MathBlock tex={`\\int \\delta[\\xi'(r)-\\xi]\\, e^{-\\beta(E+V)}\\, d^Nr = \\frac{p^{\\rm tg}(\\xi)}{P(\\xi)} \\int \\delta[\\xi'(r)-\\xi]\\, e^{-\\beta E}\\, d^Nr \\propto p^{\\rm tg}(\\xi)`} />
            </div>

            <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800/60 pb-1 mt-4">Target Distribution</h3>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <MathBlock tex={`p^{\\rm tg} = \\left[P(\\xi)\\right]^{1/\\gamma}`} />
            </div>
            <ul className="space-y-1.5 pl-4 border-l-2 border-slate-800 text-[12px]">
              <li><span className="text-amber-400 font-bold font-mono">γ = 1</span> → p<sup>tg</sup> = P(ξ), unchanged distribution.</li>
              <li><span className="text-amber-400 font-bold font-mono">γ → ∞</span> → Flat target limit, uniform distribution where all states are equiprobable.</li>
              <li><span className="text-amber-400 font-bold font-mono">1 &lt; γ &lt; ∞</span> → Flatter distribution, reduced free energy barriers.</li>
            </ul>

            <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800/60 pb-1 mt-4">Estimating P(ξ) — Weighted KDE</h3>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <MathBlock tex={`P_n(\\xi) = \\frac{\\sum_k^n w_k\\, G(\\xi, \\xi_k)}{\\sum_k^n w_k} \\qquad w_k = e^{\\beta V_{k-1}(\\xi_k)}`} />
            </div>

            <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800/60 pb-1 mt-4">Explicit Bias</h3>
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <MathBlock tex={`V_n(\\xi) = \\left(1 - \\frac{1}{\\gamma}\\right)\\frac{1}{\\beta}\\ln\\!\\left(\\frac{P_n(\\xi)}{Z_n} + \\varepsilon\\right)`} />
            </div>
            <ul className="space-y-1.5 pl-4 border-l-2 border-slate-800 font-mono text-[11px]">
              <li><span className="text-indigo-400">Z_n</span> = Σ<sub>k</sub> e<sup>βV<sub>k-1</sub>(ξ<sub>k</sub>)</sup> — normalization factor</li>
              <li><span className="text-indigo-400">ε</span> = e<sup>−βΔE/(1−1/γ)</sup> — regularization parameter</li>
            </ul>

            <h3 className="text-sm font-bold text-slate-200 border-b border-slate-800/60 pb-1 mt-4">MetaD vs OPES</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-2">
                <h4 className="font-bold text-slate-300 text-center text-xs border-b border-slate-800 pb-2">Metadynamics</h4>
                <p className="text-[11px] text-slate-500">Deposited Gaussians directly build the bias potential V<sub>n</sub>(ξ).</p>
                <p className="text-[11px] text-slate-500">Reweighting performed over the full trajectory after convergence.</p>
              </div>
              <div className="bg-amber-950/20 border border-amber-800/30 rounded-xl p-4 space-y-2">
                <h4 className="font-bold text-amber-400 text-center text-xs border-b border-amber-800/30 pb-2">OPES</h4>
                <p className="text-[11px] text-slate-400">Deposited Gaussians reconstruct the probability distribution P<sub>n</sub>(ξ).</p>
                <p className="text-[11px] text-slate-400">Reweighting performed <strong className="text-amber-300">on-the-fly</strong> during simulation.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
