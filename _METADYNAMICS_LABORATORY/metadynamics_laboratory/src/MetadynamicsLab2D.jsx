import React, { useState, useEffect, useRef, useMemo } from 'react';
import { MathBlock, MathInline } from './MathEq';
import { 
  Play, Pause, RotateCcw, Activity, TrendingUp, Layers, Plus, Trash2, 
  Crosshair, BookOpen, Thermometer, Save, Upload, Hash, Calculator, 
  Sparkles, Gauge, Zap, Check, HelpCircle, X, Sliders, RefreshCw, Eye
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

// --- Pseudo-Random Number Generator (PRNG: Mulberry32) ---
function mulberry32(a) {
  return function() {
    var t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// --- Box-Muller Transform for Independent 2D Normal Gaussian Noise N(0, 1) ---
function gaussianRandom2D(rng) {
  let u1 = rng();
  let u2 = rng();
  while (u1 === 0) u1 = rng();
  const radius = Math.sqrt(-2.0 * Math.log(u1));
  const theta = 2.0 * Math.PI * u2;
  return {
    z0: radius * Math.cos(theta),
    z1: radius * Math.sin(theta)
  };
}

// --- 2D Mathematical Presets ---
const MATH_PRESETS_2D = [
  { label: 'Symmetric 4-Well', expr: '0.2 * (x^2 - 4)^2 + 0.2 * (y^2 - 4)^2' },
  { label: 'Asymmetric 2D Double Well', expr: '0.25*x^4 - 2*x^2 + 0.5*y^2 + 0.4*x*y' },
  { label: 'Egg-Carton Periodic', expr: '2 * (cos(x) + cos(y)) + 0.1*(x^4 + y^4)' },
  { label: 'Concentric Ring Potential', expr: '0.5 * (x^2 + y^2 - 4)^2' },
  { label: 'Mueller-Brown Benchmark', expr: '0.15*(x^4 + y^4) - 5*exp(-(x+2)^2 - (y+2)^2) - 5*exp(-(x-2)^2 - (y-2)^2)' }
];

// --- Safe 2D Math Expression Parser for V(x, y) ---
const parseAndEvalMath2D = (expr, x, y) => {
  if (!expr || typeof expr !== 'string') return 0;
  try {
    let str = expr.toLowerCase().trim();
    if (!str) return 0;

    // Handle implicit multiplication: e.g. 2x -> 2*x, 2y -> 2*y, xy -> x*y, 3(x) -> 3*(x)
    str = str.replace(/([xy])\s*([xy])/g, '$1*$2');
    str = str.replace(/(\d)\s*([a-z(])/g, '$1*$2');
    str = str.replace(/(\))\s*([a-z0-9(])/g, '$1*$2');

    const tokens = [];
    let i = 0;
    while (i < str.length) {
      const ch = str[i];
      if (/\s/.test(ch)) {
        i++;
        continue;
      }
      if (/[0-9.]/.test(ch)) {
        let numStr = '';
        while (i < str.length && /[0-9.]/.test(str[i])) {
          numStr += str[i];
          i++;
        }
        tokens.push({ type: 'NUM', val: parseFloat(numStr) });
        continue;
      }
      if (/[a-z]/.test(ch)) {
        let idStr = '';
        while (i < str.length && /[a-z0-9_]/.test(str[i])) {
          idStr += str[i];
          i++;
        }
        tokens.push({ type: 'ID', val: idStr });
        continue;
      }
      if ('+-*/^()'.includes(ch)) {
        tokens.push({ type: 'OP', val: ch });
        i++;
        continue;
      }
      return 0;
    }

    let pos = 0;

    function parseExpression() {
      let left = parseTerm();
      while (pos < tokens.length && (tokens[pos].val === '+' || tokens[pos].val === '-')) {
        const op = tokens[pos++].val;
        const right = parseTerm();
        if (op === '+') left += right;
        else left -= right;
      }
      return left;
    }

    function parseTerm() {
      let left = parsePower();
      while (pos < tokens.length && (tokens[pos].val === '*' || tokens[pos].val === '/')) {
        const op = tokens[pos++].val;
        const right = parsePower();
        if (op === '*') left *= right;
        else left /= right;
      }
      return left;
    }

    function parsePower() {
      let left = parseFactor();
      if (pos < tokens.length && tokens[pos].val === '^') {
        pos++;
        const right = parsePower();
        left = Math.pow(left, right);
      }
      return left;
    }

    function parseFactor() {
      if (pos >= tokens.length) return 0;
      const tok = tokens[pos];

      if (tok.type === 'OP' && (tok.val === '-' || tok.val === '+')) {
        pos++;
        const val = parseFactor();
        return tok.val === '-' ? -val : val;
      }

      if (tok.type === 'NUM') {
        pos++;
        return tok.val;
      }

      if (tok.type === 'ID') {
        pos++;
        const id = tok.val;
        if (id === 'x') return x;
        if (id === 'y') return y;
        if (id === 'pi') return Math.PI;
        if (id === 'e') return Math.E;

        if (pos < tokens.length && tokens[pos].val === '(') {
          pos++;
          const arg = parseExpression();
          if (pos < tokens.length && tokens[pos].val === ')') pos++;
          switch (id) {
            case 'sin': return Math.sin(arg);
            case 'cos': return Math.cos(arg);
            case 'tan': return Math.tan(arg);
            case 'exp': return Math.exp(arg);
            case 'log':
            case 'ln': return Math.log(arg);
            case 'sqrt': return Math.sqrt(arg);
            case 'abs': return Math.abs(arg);
            default: return 0;
          }
        }
        return 0;
      }

      if (tok.type === 'OP' && tok.val === '(') {
        pos++;
        const val = parseExpression();
        if (pos < tokens.length && tokens[pos].val === ')') pos++;
        return val;
      }

      return 0;
    }

    const res = parseExpression();
    return isNaN(res) || !isFinite(res) ? 0 : res;
  } catch {
    return 0;
  }
};

// --- Physics: 2D Potential Energy Surface V(x, y) ---
const getPES2D = (x, y, currentWells, pesMode = 'wells', pesFunctionStr = '') => {
  if (pesMode === 'function' && pesFunctionStr.trim()) {
    return parseAndEvalMath2D(pesFunctionStr, x, y);
  }
  let energy = 0;
  energy += 0.15 * (Math.pow(x, 4) + Math.pow(y, 4)); // 2D boundary walls
  currentWells.forEach(well => {
    const distSq = Math.pow(x - well.x, 2) + Math.pow(y - well.y, 2);
    energy += -well.depth * Math.exp(-distSq / (well.width * well.width));
  });
  return energy;
};

// --- Physics: 2D Accumulated Bias Potential V_B(x, y) ---
const getBias2D = (x, y, storedBiases) => {
  let bias = 0;
  for (let g of storedBiases) {
    const distSq = Math.pow(x - g.muX, 2) + Math.pow(y - g.muY, 2);
    bias += g.h * Math.exp(-distSq / (2 * g.sigma * g.sigma));
  }
  return bias;
};

// --- Physics: 2D Conservative Force Vector (-dV/dx, -dV/dy) ---
const getForce2D = (x, y, currentBias, currentWells, pesMode = 'wells', pesFunctionStr = '') => {
  const dx = 0.001;
  const dy = 0.001;
  
  // Partial derivative d/dx
  const V_xplus = getPES2D(x + dx, y, currentWells, pesMode, pesFunctionStr);
  const V_xminus = getPES2D(x - dx, y, currentWells, pesMode, pesFunctionStr);
  const dV_pes_dx = (V_xplus - V_xminus) / (2 * dx);

  // Partial derivative d/dy
  const V_yplus = getPES2D(x, y + dy, currentWells, pesMode, pesFunctionStr);
  const V_yminus = getPES2D(x, y - dy, currentWells, pesMode, pesFunctionStr);
  const dV_pes_dy = (V_yplus - V_yminus) / (2 * dy);

  let dV_bias_dx = 0;
  let dV_bias_dy = 0;

  for (let g of currentBias) {
    const distSq = Math.pow(x - g.muX, 2) + Math.pow(y - g.muY, 2);
    const expo = Math.exp(-distSq / (2 * g.sigma * g.sigma));
    const factor = -g.h * expo / (g.sigma * g.sigma);
    dV_bias_dx += factor * (x - g.muX);
    dV_bias_dy += factor * (y - g.muY);
  }

  return {
    fx: -(dV_pes_dx + dV_bias_dx),
    fy: -(dV_pes_dy + dV_bias_dy)
  };
};

// --- Scientific Heatmap Color Gradient Mapper ---
function getHeatmapColorRGB(val, minVal, maxVal) {
  let t = (val - minVal) / (maxVal - minVal || 1);
  t = Math.max(0, Math.min(1, t));

  // 5-stop Color Palette: Dark Blue -> Teal -> Emerald -> Yellow -> Bright Red
  let r, g, b;
  if (t < 0.25) {
    const s = t / 0.25;
    r = Math.round(15 + s * (2 - 15));
    g = Math.round(23 + s * (132 - 23));
    b = Math.round(42 + s * (199 - 42));
  } else if (t < 0.5) {
    const s = (t - 0.25) / 0.25;
    r = Math.round(2 + s * (16 - 2));
    g = Math.round(132 + s * (185 - 132));
    b = Math.round(199 + s * (129 - 199));
  } else if (t < 0.75) {
    const s = (t - 0.5) / 0.25;
    r = Math.round(16 + s * (245 - 16));
    g = Math.round(185 + s * (158 - 185));
    b = Math.round(129 + s * (11 - 129));
  } else {
    const s = (t - 0.75) / 0.25;
    r = Math.round(245 + s * (239 - 245));
    g = Math.round(158 + s * (68 - 158));
    b = Math.round(11 + s * (68 - 11));
  }
  return `rgb(${r}, ${g}, ${b})`;
}

const MetadynamicsLab2D = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [timeStep, setTimeStep] = useState(0);
  const [showGuideModal, setShowGuideModal] = useState(false);

  // PES Mode & Canvas View Mode
  const [pesMode, setPesMode] = useState('wells'); // 'wells' | 'function'
  const [pesFunctionStr, setPesFunctionStr] = useState('0.2 * (x^2 - 4)^2 + 0.2 * (y^2 - 4)^2');
  const [canvasViewMode, setCanvasViewMode] = useState('pes'); // 'pes' | 'total' | 'bias' | 'fes'

  // 2D Wells State
  const [wells, setWells] = useState([
    { id: 1, x: -2, y: -2, depth: 8, width: 1.0 },
    { id: 2, x: 2, y: 2, depth: 8, width: 1.0 }
  ]);

  // Metadynamics Parameters
  const [gaussianHeight, setGaussianHeight] = useState(0.5);
  const [gaussianWidth, setGaussianWidth] = useState(0.5);
  const [depositionStride, setDepositionStride] = useState(20);
  const [temperature, setTemperature] = useState(0.8);
  const [isWellTempered, setIsWellTempered] = useState(false);
  const [biasFactor, setBiasFactor] = useState(10);

  // 2D Walker Position & Trajectory
  const [walkerPos, setWalkerPos] = useState({ x: -2, y: -2 });
  const [trajectory, setTrajectory] = useState([{ x: -2, y: -2 }]);
  const [biasPotentials, setBiasPotentials] = useState([]);
  const [currentDepositionHeight, setCurrentDepositionHeight] = useState(0.5);
  const [colvarHistory2D, setColvarHistory2D] = useState([{ step: 0, x: -2, y: -2 }]);

  // 1D Projections Mode (computed inside canvas useEffect)
  const [projMode, setProjMode] = useState('int'); // 'int' | 'min'


  // RNG & Seed
  const [seed, setSeed] = useState(12345);
  const [useFixedSeed, setUseFixedSeed] = useState(false);
  const rngRef = useRef(Math.random);

  const canvasRef = useRef(null);
  const savedCallback = useRef();
  const fileInputRef = useRef(null);

  const initRNG = (currentSeed) => {
    rngRef.current = mulberry32(currentSeed);
  };

  // --- Session Export / Import ---
  const handleExport = () => {
    const data = {
      version: "2.0_2D",
      pesMode,
      pesFunctionStr,
      wells,
      biasPotentials,
      walkerPos,
      trajectory,
      colvarHistory2D,
      timeStep,
      config: {
        gaussianHeight,
        gaussianWidth,
        depositionStride,
        temperature,
        isWellTempered,
        biasFactor,
        seed,
        useFixedSeed
      }
    };

    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(data, null, 2))}`;
    const link = document.createElement("a");
    link.href = jsonString;
    link.download = `metadynamics_2D_session_${new Date().toISOString().slice(0,10)}.json`;
    link.click();
  };

  const handleImport = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        setIsRunning(false);
        if (data.pesMode) setPesMode(data.pesMode);
        if (data.pesFunctionStr) setPesFunctionStr(data.pesFunctionStr);
        setWells(data.wells || []);
        setBiasPotentials(data.biasPotentials || []);
        if (data.walkerPos) setWalkerPos(data.walkerPos);
        if (data.trajectory) setTrajectory(data.trajectory);
        if (data.colvarHistory2D) setColvarHistory2D(data.colvarHistory2D);
        setTimeStep(data.timeStep || 0);

        const loadedSeed = data.config?.seed ?? data.seed ?? seed;
        const loadedFixed = data.config?.useFixedSeed ?? true;
        setSeed(loadedSeed);
        setUseFixedSeed(loadedFixed);

        if (data.config) {
          setGaussianHeight(data.config.gaussianHeight);
          setGaussianWidth(data.config.gaussianWidth);
          setDepositionStride(data.config.depositionStride);
          setTemperature(data.config.temperature);
          setIsWellTempered(data.config.isWellTempered);
          setBiasFactor(data.config.biasFactor);
        }

        initRNG(loadedSeed);
      } catch {
        alert("Invalid JSON 2D session file.");
      }
    };
    reader.readAsText(file);
    e.target.value = null;
  };

  // --- Well Controls ---
  const addWell = () => {
    const newId = wells.length > 0 ? Math.max(...wells.map(w => w.id)) + 1 : 1;
    setWells([...wells, { id: newId, x: 0, y: 0, depth: 6, width: 1.0 }]);
    handleReset();
  };

  const removeWell = (id) => {
    setWells(wells.filter(w => w.id !== id));
    handleReset();
  };

  const updateWell = (id, field, value) => {
    setWells(wells.map(w => w.id === id ? { ...w, [field]: parseFloat(value) } : w));
  };

  // --- Langevin 2D Step ---
  const stepSimulation = () => {
    let currentX = walkerPos.x;
    let currentY = walkerPos.y;

    const force = getForce2D(currentX, currentY, biasPotentials, wells, pesMode, pesFunctionStr);
    const dt = 0.05;

    const MAX_FORCE = 15;
    let fx = Math.max(-MAX_FORCE, Math.min(MAX_FORCE, force.fx));
    let fy = Math.max(-MAX_FORCE, Math.min(MAX_FORCE, force.fy));

    const noisePair = gaussianRandom2D(rngRef.current);
    const noiseFactor = Math.sqrt(2 * temperature * dt);

    let newX = currentX + fx * dt + noiseFactor * noisePair.z0;
    let newY = currentY + fy * dt + noiseFactor * noisePair.z1;

    newX = Math.max(-4.5, Math.min(4.5, newX));
    newY = Math.max(-4.5, Math.min(4.5, newY));

    const newPos = { x: newX, y: newY };
    setWalkerPos(newPos);
    setTrajectory(prev => [...prev.slice(-300), newPos]);

    setTimeStep((prevTime) => {
      const nextTime = prevTime + 1;
      setColvarHistory2D(prev => [...prev.slice(-2000), { step: nextTime, x: parseFloat(newX.toFixed(3)), y: parseFloat(newY.toFixed(3)) }]);

      if (nextTime % depositionStride === 0) {
        let newHeight = gaussianHeight;

        if (isWellTempered) {
          const currentBiasV = getBias2D(newX, newY, biasPotentials);
          const deltaT = temperature * (biasFactor - 1);
          if (deltaT > 0) {
            newHeight = gaussianHeight * Math.exp(-currentBiasV / deltaT);
          }
        }

        setCurrentDepositionHeight(newHeight);
        setBiasPotentials(prev => [
          ...prev,
          { muX: newX, muY: newY, h: newHeight, sigma: gaussianWidth }
        ]);
      }
      return nextTime;
    });
  };

  useEffect(() => {
    savedCallback.current = stepSimulation;
  });

  useEffect(() => {
    if (isRunning) {
      const tick = () => {
        if (savedCallback.current) savedCallback.current();
      };
      const id = setInterval(tick, 40);
      return () => clearInterval(id);
    }
  }, [isRunning]);

  const handleReset = () => {
    setIsRunning(false);
    setTimeStep(0);
    setBiasPotentials([]);
    setCurrentDepositionHeight(gaussianHeight);

    let nextSeed = seed;
    if (!useFixedSeed) {
      const array = new Uint32Array(1);
      crypto.getRandomValues(array);
      nextSeed = array[0] % 1000000;
      setSeed(nextSeed);
    }

    initRNG(nextSeed);
    const startX = pesMode === 'wells' ? (wells.length > 0 ? wells[0].x : -2) : -2;
    const startY = pesMode === 'wells' ? (wells.length > 0 ? wells[0].y : -2) : -2;
    const initialPos = { x: startX, y: startY };
    setWalkerPos(initialPos);
    setTrajectory([initialPos]);
    setColvarHistory2D([{ step: 0, x: startX, y: startY }]);
  };

  const generateNewSeed = () => {
    const array = new Uint32Array(1);
    crypto.getRandomValues(array);
    const newSeed = array[0] % 1000000;
    setSeed(newSeed);
    setUseFixedSeed(true);
    initRNG(newSeed);
    handleReset();
  };

  useEffect(() => {
    initRNG(seed);
  }, [seed]);

  // --- Render 2D Canvas: Heatmap + Projections (unified, pixel-perfect) ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const W = canvas.width;   // 680
    const H = canvas.height;  // 430

    // ── Layout margins ────────────────────────────────────────
    const ML = 50;   // left:   Y-axis tick labels for heatmap
    const MB = 35;   // bottom: X-axis tick labels for heatmap
    const MT = 85;   // top:    F(CV₁) projection strip
    const MR = 115;  // right:  F(CV₂) projection strip

    const hx0 = ML, hx1 = W - MR;   // heatmap x bounds
    const hy0 = MT, hy1 = H - MB;   // heatmap y bounds
    const hW  = hx1 - hx0;          // heatmap pixel width
    const hH  = hy1 - hy0;          // heatmap pixel height

    // CV ↔ canvas pixel transforms (inside heatmap area)
    // toHX: cv1 ∈ [-4.5,4.5] → px ∈ [hx0, hx1]
    // toHY: cv2=+4.5 → hy0 (TOP), cv2=-4.5 → hy1 (BOTTOM)
    const toHX = (x) => hx0 + ((x + 4.5) / 9.0) * hW;
    const toHY = (y) => hy0 + ((4.5 - y) / 9.0) * hH;

    // ── Clear canvas ─────────────────────────────────────────
    ctx.fillStyle = '#020817';
    ctx.fillRect(0, 0, W, H);

    // ── 1. Compute 2D FES grid (res×res) ─────────────────────
    const res = 60;
    const gs = 9.0 / res;

    const gridVals = new Float64Array(res * res);
    let gMin = Infinity, gMax = -Infinity;

    for (let gy = 0; gy < res; gy++) {
      const cy = 4.5 - gy * gs;
      for (let gx = 0; gx < res; gx++) {
        const cx = -4.5 + gx * gs;
        const pes  = getPES2D(cx, cy, wells, pesMode, pesFunctionStr);
        const bias = getBias2D(cx, cy, biasPotentials);
        let v;
        if      (canvasViewMode === 'pes')   v = pes;
        else if (canvasViewMode === 'bias')  v = bias;
        else if (canvasViewMode === 'total') v = pes + bias;
        else v = (isWellTempered && biasFactor > 1)
          ? -(biasFactor / (biasFactor - 1)) * bias
          : -bias;
        gridVals[gy * res + gx] = v;
        if (v < gMin) gMin = v;
        if (v > gMax) gMax = v;
      }
    }

    // ── 2. Draw heatmap ──────────────────────────────────────────
    const cW = hW / res;
    const cH = hH / res;
    for (let gy = 0; gy < res; gy++) {
      for (let gx = 0; gx < res; gx++) {
        ctx.fillStyle = getHeatmapColorRGB(gridVals[gy * res + gx], gMin, gMax);
        ctx.fillRect(hx0 + gx * cW, hy0 + gy * cH, cW + 0.5, cH + 0.5);
      }
    }

    // ── 3. Subtle grid lines ─────────────────────────────────────
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 8; i++) {
      const xp = hx0 + (i / 8) * hW;
      const yp = hy0 + (i / 8) * hH;
      ctx.moveTo(xp, hy0); ctx.lineTo(xp, hy1);
      ctx.moveTo(hx0, yp); ctx.lineTo(hx1, yp);
    }
    ctx.stroke();

    // ── 4. Compute 1D projections from same grid ─────────────────
    // These are the physically correct projections of the 2D surface:
    //   F(CV₁) = -kT ln ∫ exp(-F(x,y)/kT) dy   [integrate over y for each x]
    //   F(CV₂) = -kT ln ∫ exp(-F(x,y)/kT) dx   [integrate over x for each y]
    const kBT = Math.max(0.01, temperature);

    // F(CV₁): for each gx column, integrate/min over all gy rows
    const fProjX = new Float64Array(res);
    for (let gx = 0; gx < res; gx++) {
      if (projMode === 'min') {
        let m = Infinity;
        for (let gy = 0; gy < res; gy++) { const v = gridVals[gy*res+gx]; if (v < m) m = v; }
        fProjX[gx] = m;
      } else {
        let S = 0;
        for (let gy = 0; gy < res; gy++) S += Math.exp(-gridVals[gy*res+gx] / kBT);
        fProjX[gx] = -kBT * Math.log(Math.max(S, 1e-300));
      }
    }
    let minPX = fProjX[0]; for (const v of fProjX) if (v < minPX) minPX = v;
    let maxPX = 0; for (let i = 0; i < res; i++) { fProjX[i] -= minPX; if (fProjX[i] > maxPX) maxPX = fProjX[i]; }

    // F(CV₂): for each gy row, integrate/min over all gx columns
    // gy=0 → y=+4.5 (TOP of heatmap = hy0), gy=res-1 → y≈-4.5 (BOTTOM = hy1)
    const fProjY = new Float64Array(res);
    for (let gy = 0; gy < res; gy++) {
      if (projMode === 'min') {
        let m = Infinity;
        for (let gx = 0; gx < res; gx++) { const v = gridVals[gy*res+gx]; if (v < m) m = v; }
        fProjY[gy] = m;
      } else {
        let S = 0;
        for (let gx = 0; gx < res; gx++) S += Math.exp(-gridVals[gy*res+gx] / kBT);
        fProjY[gy] = -kBT * Math.log(Math.max(S, 1e-300));
      }
    }
    let minPY = fProjY[0]; for (const v of fProjY) if (v < minPY) minPY = v;
    let maxPY = 0; for (let i = 0; i < res; i++) { fProjY[i] -= minPY; if (fProjY[i] > maxPY) maxPY = fProjY[i]; }

    // ── 5. Draw F(CV₁) — top strip ──────────────────────────────
    // Strip: x ∈ [hx0, hx1], y ∈ [4, hy0-2]
    // F=0 → bottom of strip (touching heatmap border)
    // F=max → near top of strip
    // x of point gx = hx0 + (gx+0.5)*cW  ←  matches heatmap column center exactly
    const sT_top = 4;
    const sT_bot = hy0 - 2;
    const sT_H   = sT_bot - sT_top;

    ctx.fillStyle = 'rgba(2, 8, 23, 0.55)';
    ctx.fillRect(hx0, sT_top, hW, sT_H);

    if (maxPX > 1e-6) {
      const pts1 = [];
      for (let gx = 0; gx < res; gx++) {
        pts1.push({
          px: hx0 + (gx + 0.5) * cW,
          py: sT_bot - (fProjX[gx] / maxPX) * (sT_H - 6)
        });
      }
      // Filled gradient area (baseline = sT_bot)
      ctx.beginPath();
      ctx.moveTo(pts1[0].px, sT_bot);
      for (const p of pts1) ctx.lineTo(p.px, p.py);
      ctx.lineTo(pts1[res-1].px, sT_bot);
      ctx.closePath();
      const g1 = ctx.createLinearGradient(0, sT_top, 0, sT_bot);
      g1.addColorStop(0, 'rgba(6, 182, 212, 0.45)');
      g1.addColorStop(1, 'rgba(6, 182, 212, 0.06)');
      ctx.fillStyle = g1;
      ctx.fill();
      // Line
      ctx.beginPath();
      ctx.moveTo(pts1[0].px, pts1[0].py);
      for (const p of pts1) ctx.lineTo(p.px, p.py);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1.8;
      ctx.lineJoin = 'round';
      ctx.stroke();
    }

    // Label
    ctx.font = 'bold 9px monospace';
    ctx.fillStyle = '#06b6d4';
    ctx.textAlign = 'left';
    ctx.fillText(
      `F(CV\u2081) 1D Projection  [${projMode === 'int' ? 'k\u2082T Int.' : 'Min. Path'}]`,
      hx0 + 4, sT_top + 12
    );
    // Separator line between top strip and heatmap
    ctx.strokeStyle = 'rgba(6, 182, 212, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx0, hy0); ctx.lineTo(hx1, hy0); ctx.stroke();

    // ── 6. Draw F(CV₂) — right strip ────────────────────────────
    // Strip: x ∈ [hx1+3, W-4], y ∈ [hy0, hy1]
    // y of point gy = hy0 + (gy+0.5)*cH  ← matches heatmap row center exactly
    // F=0 → left edge of strip (touching heatmap border)
    // F=max → extends toward right
    const sR_lft = hx1 + 3;
    const sR_rgt = W - 4;
    const sR_W   = sR_rgt - sR_lft;

    ctx.fillStyle = 'rgba(2, 8, 23, 0.55)';
    ctx.fillRect(sR_lft, hy0, sR_W, hH);

    if (maxPY > 1e-6) {
      const pts2 = [];
      for (let gy = 0; gy < res; gy++) {
        pts2.push({
          // CRITICAL: same y as heatmap row center → alignment by construction
          py: hy0 + (gy + 0.5) * cH,
          px: sR_lft + (fProjY[gy] / maxPY) * (sR_W - 6)
        });
      }
      // Filled gradient area (baseline = sR_lft)
      ctx.beginPath();
      ctx.moveTo(sR_lft, pts2[0].py);
      for (const p of pts2) ctx.lineTo(p.px, p.py);
      ctx.lineTo(sR_lft, pts2[res-1].py);
      ctx.closePath();
      const g2 = ctx.createLinearGradient(sR_lft, 0, sR_rgt, 0);
      g2.addColorStop(0, 'rgba(192, 132, 252, 0.06)');
      g2.addColorStop(1, 'rgba(192, 132, 252, 0.45)');
      ctx.fillStyle = g2;
      ctx.fill();
      // Line
      ctx.beginPath();
      ctx.moveTo(pts2[0].px, pts2[0].py);
      for (const p of pts2) ctx.lineTo(p.px, p.py);
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 1.8;
      ctx.lineJoin = 'round';
      ctx.stroke();
    }

    // Label
    ctx.save();
    ctx.font = 'bold 9px monospace';
    ctx.fillStyle = '#c084fc';
    ctx.textAlign = 'center';
    ctx.translate(sR_lft + sR_W / 2, hy0 - 5);
    ctx.fillText('F(CV\u2082) 1D', 0, 0);
    ctx.restore();
    // Separator line between heatmap and right strip
    ctx.strokeStyle = 'rgba(192, 132, 252, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx1, hy0); ctx.lineTo(hx1, hy1); ctx.stroke();

    // ── 7. Axis ticks and labels ─────────────────────────────────
    const axisTicks = [-4.0, -2.0, 0, 2.0, 4.0];
    ctx.font = 'bold 10px Inter, monospace';

    // X axis (CV₁) — below heatmap
    for (const tx of axisTicks) {
      const cx = toHX(tx);
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.fillRect(cx - 0.5, hy1, 1, 5);
      ctx.fillStyle = 'rgba(203, 213, 225, 0.85)';
      ctx.textAlign = 'center';
      ctx.fillText(tx > 0 ? `+${tx.toFixed(1)}` : `${tx.toFixed(1)}`, cx, hy1 + 16);
    }

    // Y axis (CV₂) — left of heatmap
    for (const ty of axisTicks) {
      const cy = toHY(ty);
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.fillRect(hx0 - 5, cy - 0.5, 5, 1);
      ctx.fillStyle = 'rgba(203, 213, 225, 0.85)';
      ctx.textAlign = 'right';
      ctx.fillText(ty > 0 ? `+${ty.toFixed(1)}` : `${ty.toFixed(1)}`, hx0 - 7, cy + 4);
    }

    // CV₁ badge (bottom-right of heatmap)
    ctx.font = 'bold 11px Inter, monospace';
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.fillRect(hx1 - 74, hy1 - 24, 68, 20);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
    ctx.lineWidth = 1;
    ctx.strokeRect(hx1 - 74, hy1 - 24, 68, 20);
    ctx.fillStyle = '#38bdf8';
    ctx.textAlign = 'center';
    ctx.fillText('CV\u2081 (x)', hx1 - 40, hy1 - 10);

    // CV₂ badge (top-left of heatmap)
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.fillRect(hx0 + 4, hy0 + 4, 68, 20);
    ctx.strokeStyle = 'rgba(192, 132, 252, 0.6)';
    ctx.strokeRect(hx0 + 4, hy0 + 4, 68, 20);
    ctx.fillStyle = '#c084fc';
    ctx.textAlign = 'center';
    ctx.fillText('CV\u2082 (y)', hx0 + 38, hy0 + 18);

    // ── 8. Trajectory ────────────────────────────────────────────
    if (trajectory.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255,255,255,0.9)';
      ctx.lineWidth = 2.5;
      ctx.moveTo(toHX(trajectory[0].x), toHY(trajectory[0].y));
      for (const p of trajectory) ctx.lineTo(toHX(p.x), toHY(p.y));
      ctx.stroke();
    }

    // ── 9. Walker glowing dot ────────────────────────────────────
    const wx = toHX(walkerPos.x);
    const wy = toHY(walkerPos.y);
    ctx.beginPath();
    ctx.arc(wx, wy, 12, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(6, 182, 212, 0.3)';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(wx, wy, 6, 0, 2 * Math.PI);
    ctx.fillStyle = '#06b6d4';
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();

  }, [timeStep, walkerPos, trajectory, canvasViewMode, wells, pesMode, pesFunctionStr, biasPotentials, isWellTempered, biasFactor, projMode, temperature]);


  // Click on Canvas to reposition walker (updated for new margins)
  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();

    // Scale CSS pixels to canvas pixels
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cpx = (e.clientX - rect.left) * scaleX;
    const cpy = (e.clientY - rect.top) * scaleY;

    // Layout constants (must match canvas useEffect)
    const ML = 50, MB = 35, MT = 85, MR = 115;
    const hx0 = ML, hx1 = canvas.width - MR;
    const hy0 = MT, hy1 = canvas.height - MB;
    const hW = hx1 - hx0, hH = hy1 - hy0;

    // Only respond to clicks inside the heatmap area
    if (cpx < hx0 || cpx > hx1 || cpy < hy0 || cpy > hy1) return;

    const x = -4.5 + ((cpx - hx0) / hW) * 9.0;
    const y = 4.5 - ((cpy - hy0) / hH) * 9.0;

    const newPos = { x: parseFloat(x.toFixed(2)), y: parseFloat(y.toFixed(2)) };
    setWalkerPos(newPos);
    setTrajectory(prev => [...prev, newPos]);
  };

  const currentPES = getPES2D(walkerPos.x, walkerPos.y, wells, pesMode, pesFunctionStr);
  const currentBiasVal = getBias2D(walkerPos.x, walkerPos.y, biasPotentials);
  const currentForce = getForce2D(walkerPos.x, walkerPos.y, biasPotentials, wells, pesMode, pesFunctionStr);
  const forceMag = Math.sqrt(currentForce.fx * currentForce.fx + currentForce.fy * currentForce.fy);

  return (
    <div className="flex flex-col w-full space-y-3">
      
      {/* 2D Header Bar */}
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3 relative overflow-hidden">
        <div className="flex items-center gap-4 z-10">
          <div className="p-3 bg-gradient-to-br from-purple-500/20 to-indigo-600/20 border border-purple-500/30 rounded-xl text-purple-400 shadow-lg shadow-purple-500/10">
            <Layers size={28} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-purple-100 to-indigo-300 bg-clip-text text-transparent">
                2D Metadynamics Simulation Lab
              </h1>
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-purple-950 text-purple-300 border border-purple-800/60 rounded-full">
                2D Langevin • Canvas Heatmap Engine
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              Interactive 2D Collective Variable (CV_x, CV_y) Langevin Diffusion & Free Energy Surfaces
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end z-10">
          
          <div className="hidden sm:flex items-center gap-2 mr-2 bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800/80 text-xs">
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-white uppercase font-semibold">Steps</span>
              <span className="font-mono font-bold text-white">{timeStep}</span>
            </div>
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-white uppercase font-semibold">Hills</span>
              <span className="font-mono font-bold text-purple-400">{biasPotentials.length}</span>
            </div>
            <div className="flex flex-col items-center px-2">
              <span className="text-[10px] text-white uppercase font-semibold">Height W(t)</span>
              <span className="font-mono font-bold text-white">{currentDepositionHeight.toFixed(3)}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
            <input type="file" ref={fileInputRef} onChange={handleImport} accept=".json" className="hidden" />
            <button onClick={handleExport} className="p-2 text-slate-400 hover:text-purple-400 hover:bg-slate-800/60 rounded-lg transition-colors" title="Save 2D Session (JSON)">
              <Save size={18} />
            </button>
            <button onClick={() => fileInputRef.current.click()} className="p-2 text-slate-400 hover:text-purple-400 hover:bg-slate-800/60 rounded-lg transition-colors" title="Load 2D Session (JSON)">
              <Upload size={18} />
            </button>
          </div>

          <button onClick={() => setShowGuideModal(true)} className="py-2 px-3.5 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm">
            <BookOpen size={16} className="text-purple-400" /> <span>2D Theory</span>
          </button>

          <button onClick={handleReset} className="p-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 rounded-xl transition-all shadow-sm" title="Reset Simulation">
            <RotateCcw size={18} />
          </button>

          <button onClick={() => setIsRunning(!isRunning)} className={`py-2.5 px-6 rounded-xl font-bold text-xs tracking-wide shadow-lg flex items-center gap-2 transition-all ${
            isRunning 
              ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-amber-500/20 hover:from-amber-400 hover:to-amber-500' 
              : 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-purple-500/20 hover:from-purple-400 hover:to-indigo-500'
          }`}>
            {isRunning ? <><Pause size={18} /> PAUSE</> : <><Play size={18} /> SIMULATE 2D</>}
          </button>
        </div>
      </header>

      {/* Main 2D Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: 2D Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          
          {/* Card 1: 2D PES Configuration */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="flex justify-between items-center pb-2.5 border-b border-slate-800/80">
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Crosshair size={16} className="text-purple-400" /> 2D Surface (PES)
              </h3>
              
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                <button onClick={() => { setPesMode('wells'); handleReset(); }} className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${pesMode === 'wells' ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                  2D Wells
                </button>
                <button onClick={() => { setPesMode('function'); handleReset(); }} className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${pesMode === 'function' ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                  Math V(x,y)
                </button>
              </div>
            </div>

            {pesMode === 'wells' ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">2D Gaussian Wells</span>
                  <button onClick={addWell} className="text-xs bg-purple-950 text-purple-300 hover:bg-purple-900/60 border border-purple-800/50 px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold transition-colors">
                    <Plus size={14} /> Add 2D Well
                  </button>
                </div>
                <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                  {wells.map((well, idx) => (
                    <div key={well.id} className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-purple-400"></span> Well #{idx + 1}
                        </span>
                        <button onClick={() => removeWell(well.id)} className="text-slate-500 hover:text-red-400 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs text-slate-400">
                        <div>
                          <span className="block mb-1">Pos X: <span className="font-mono text-purple-300">{well.x}</span></span>
                          <input type="range" min="-3.5" max="3.5" step="0.1" value={well.x} onChange={(e) => updateWell(well.id, 'x', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"/>
                        </div>
                        <div>
                          <span className="block mb-1">Pos Y: <span className="font-mono text-purple-300">{well.y}</span></span>
                          <input type="range" min="-3.5" max="3.5" step="0.1" value={well.y} onChange={(e) => updateWell(well.id, 'y', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"/>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs text-slate-400 pt-1">
                        <div>
                          <span className="block mb-1">Depth: <span className="font-mono text-indigo-300">{well.depth}</span></span>
                          <input type="range" min="1" max="15" step="0.5" value={well.depth} onChange={(e) => updateWell(well.id, 'depth', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-400"/>
                        </div>
                        <div>
                          <span className="block mb-1">Width (σ): <span className="font-mono text-cyan-300">{well.width}</span></span>
                          <input type="range" min="0.2" max="2.0" step="0.1" value={well.width} onChange={(e) => updateWell(well.id, 'width', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"/>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <Calculator size={14} className="text-purple-400" /> Expression V(x, y):
                  </label>
                  <input type="text" value={pesFunctionStr} onChange={(e) => { setPesFunctionStr(e.target.value); handleReset(); }} placeholder="e.g. 0.2*(x^2-4)^2 + 0.2*(y^2-4)^2" className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-mono text-purple-300 focus:ring-2 focus:ring-purple-500/50 outline-none" />
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Load 2D Preset Function:</label>
                  <select onChange={(e) => { if (e.target.value) { setPesFunctionStr(e.target.value); handleReset(); } }} value={pesFunctionStr} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 outline-none">
                    {MATH_PRESETS_2D.map((preset, idx) => (
                      <option key={idx} value={preset.expr}>{preset.label} — {preset.expr}</option>
                    ))}
                  </select>
                </div>

                <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                  <span className="font-semibold text-slate-300 block">Supported Variables & Syntax:</span>
                  <div className="font-mono text-[10px] text-slate-400 leading-relaxed">
                    x, y | +, -, *, /, ^ | sin, cos, exp, log, sqrt, abs | pi, e
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Card 2: 2D Metadynamics Hyperparameters */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="pb-2 border-b border-slate-800/80 font-semibold text-xs text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Layers size={16} className="text-purple-400" /> Metadynamics Parameters
            </div>
            
            <div className="space-y-4">
              <div className="bg-gradient-to-br from-slate-950 to-indigo-950/30 p-3.5 rounded-xl border border-indigo-900/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                    <Thermometer size={16} className="text-indigo-400" /> Well-Tempered MetaD
                  </span>
                  <div className={`w-10 h-5 rounded-full cursor-pointer relative transition-colors ${isWellTempered ? 'bg-indigo-600' : 'bg-slate-800'}`} onClick={() => { setIsWellTempered(!isWellTempered); handleReset(); }}>
                    <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all shadow-md ${isWellTempered ? 'left-5.5' : 'left-0.5'}`}></div>
                  </div>
                </div>

                {isWellTempered && (
                  <div className="mt-3.5 pt-3 border-t border-indigo-900/40 space-y-2">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span>Bias Factor (γ)</span>
                      <span className="font-mono font-bold text-indigo-400">{biasFactor}</span>
                    </div>
                    <input type="range" min="2" max="30" step="1" value={biasFactor} onChange={(e) => { setBiasFactor(parseInt(e.target.value)); handleReset(); }} className="w-full h-1.5 bg-indigo-900/60 rounded-lg appearance-none cursor-pointer accent-indigo-400"/>
                  </div>
                )}
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Initial Hill Height (W₀)</span>
                  <span className="font-mono font-semibold text-purple-400">{gaussianHeight.toFixed(2)} kJ/mol</span>
                </div>
                <input type="range" min="0.1" max="2.0" step="0.1" value={gaussianHeight} onChange={(e) => setGaussianHeight(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"/>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Hill Radial Width (σ)</span>
                  <span className="font-mono font-semibold text-cyan-400">{gaussianWidth.toFixed(2)}</span>
                </div>
                <input type="range" min="0.1" max="1.5" step="0.05" value={gaussianWidth} onChange={(e) => setGaussianWidth(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"/>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Thermal Energy (k<sub>B</sub>T)</span>
                  <span className="font-mono font-semibold text-amber-400">{temperature.toFixed(2)}</span>
                </div>
                <input type="range" min="0.1" max="3.0" step="0.1" value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"/>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Deposition Stride (τ)</span>
                  <span className="font-mono font-semibold text-emerald-400">{depositionStride} steps</span>
                </div>
                <input type="range" min="5" max="50" step="5" value={depositionStride} onChange={(e) => setDepositionStride(parseInt(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"/>
              </div>
            </div>
          </div>

          {/* Card 3: Reproducibility */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800 text-xs text-slate-400 font-semibold uppercase tracking-wider">
              <span className="flex items-center gap-1.5"><Hash size={14} className="text-purple-400" /> Reproducibility</span>
              <button onClick={generateNewSeed} className="text-[11px] text-purple-400 hover:text-purple-300 flex items-center gap-1 font-mono font-normal">
                <RefreshCw size={12} /> New Seed
              </button>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-[11px] text-slate-400 mb-1 font-medium">RNG Seed</label>
                <input type="number" value={seed} onChange={(e) => { const s = parseInt(e.target.value) || 0; setSeed(s); setUseFixedSeed(true); setIsRunning(false); initRNG(s); }} className="w-full bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-xs font-mono text-center text-slate-200" />
              </div>
              <div className="flex items-center gap-2 pt-4">
                <input type="checkbox" id="fixedSeedCheck2D" checked={useFixedSeed} onChange={(e) => setUseFixedSeed(e.target.checked)} className="rounded bg-slate-950 border-slate-700 text-purple-500 focus:ring-purple-500 cursor-pointer" />
                <label htmlFor="fixedSeedCheck2D" className="text-xs text-slate-300 cursor-pointer select-none">Fixed Seed</label>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: 2D Stage Canvas (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-3">
          
          {/* 2D Heatmap Stage + Integrated Top CV_x & Right CV_y Projections */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3.5 shadow-2xl space-y-2">
            
            {/* Header Controls: Canvas View Mode & Projection Mode Toggle */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Eye size={16} className="text-purple-400" />
                <h3 className="font-bold text-slate-100 text-sm">
                  2D Energy Surface & Integrated 1D Projections
                </h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {/* Projection Mode Toggle */}
                <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                  <button
                    onClick={() => setProjMode('int')}
                    className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold transition-all ${
                      projMode === 'int'
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                    title="Boltzmann integration: F(s₁) = -k_B T ln Σ exp(-F/k_B T)"
                  >
                    Boltzmann (k<sub>B</sub>T)
                  </button>
                  <button
                    onClick={() => setProjMode('min')}
                    className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold transition-all ${
                      projMode === 'min'
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                    title="Minimum energy path: F_min(s₁) = min_s₂ F(s₁, s₂)"
                  >
                    Minimum Path
                  </button>
                </div>

                {/* Canvas View Mode Selector */}
                <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                  <button onClick={() => setCanvasViewMode('pes')} className={`px-2 py-0.5 rounded-lg text-xs font-semibold transition-all ${canvasViewMode === 'pes' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                    Original V(x,y)
                  </button>
                  <button onClick={() => setCanvasViewMode('total')} className={`px-2 py-0.5 rounded-lg text-xs font-semibold transition-all ${canvasViewMode === 'total' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                    Total V + V<sub>B</sub>
                  </button>
                  <button onClick={() => setCanvasViewMode('bias')} className={`px-2 py-0.5 rounded-lg text-xs font-semibold transition-all ${canvasViewMode === 'bias' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                    Bias V<sub>B</sub>
                  </button>
                  <button onClick={() => setCanvasViewMode('fes')} className={`px-2 py-0.5 rounded-lg text-xs font-semibold transition-all ${canvasViewMode === 'fes' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
                    Estimated FES
                  </button>
                </div>
              </div>
            </div>

            {/*
              Unified canvas (680×430): heatmap + F(CV₁) top strip + F(CV₂) right strip.
              All drawn in canvas pixel coordinates → pixel-perfect alignment.
              Layout:
                Left margin (ML=50):  Y-axis tick labels (CV₂)
                Top strip (MT=85):    F(CV₁) projection (integrate/min over y)
                Heatmap (515×310):    2D FES coloured surface
                Right strip (MR=115): F(CV₂) projection (integrate/min over x)
                Bottom margin (MB=35): X-axis tick labels (CV₁)
            */}
            <div style={{ background: '#020817', borderRadius: 16, border: '1px solid #1e293b', overflow: 'hidden', position: 'relative' }}>
              <canvas
                ref={canvasRef}
                width={680}
                height={430}
                onClick={handleCanvasClick}
                style={{ display: 'block', width: '100%', cursor: 'crosshair' }}
              />
            </div>


            {/* Heatmap Legend Bar */}
            <div className="mt-1 flex justify-between items-center text-[10px] text-slate-400 px-2 font-mono">
              <span>Min Energy (Basin)</span>
              <div className="h-1.5 w-40 rounded-full bg-gradient-to-r from-slate-900 via-sky-600 via-emerald-500 via-amber-400 to-red-500"></div>
              <span>Max Energy (Barrier)</span>
            </div>
          </div>


          {/* 2D COLVAR Time-Series Chart Card */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl space-y-1">

            <div className="flex justify-between items-center pb-1 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-slate-100 flex items-center gap-2 text-xs">
                  <Activity size={14} className="text-purple-400" />
                  2D COLVAR Time-Series Trajectories: CV<sub>x</sub>(t) & CV<sub>y</sub>(t)
                </h3>
              </div>
              <div className="flex items-center gap-2 text-[10px] font-mono">
                <span className="text-cyan-400 font-bold">CV<sub>x</sub> = {walkerPos.x.toFixed(2)}</span>
                <span className="text-purple-400 font-bold">CV<sub>y</sub> = {walkerPos.y.toFixed(2)}</span>
              </div>
            </div>

            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={colvarHistory2D} margin={{ top: 5, right: 20, left: 15, bottom: 22 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                  <XAxis 
                    dataKey="step" 
                    type="number"
                    domain={[0, 'auto']}
                    stroke="#94a3b8" 
                    fontSize={9} 
                    label={{ value: 'Step (t)', position: 'bottom', offset: 8, fill: '#94a3b8', fontSize: 10 }} 
                  />
                  <YAxis 
                    domain={[-4.5, 4.5]} 
                    stroke="#94a3b8" 
                    fontSize={9} 
                    label={{ value: 'CV Position', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '11px', padding: '6px 10px' }} 
                    labelStyle={{ color: '#c084fc', fontWeight: 'bold' }} 
                  />
                  <Legend verticalAlign="top" height={22} wrapperStyle={{ fontSize: '10px' }} />
                  <Line 
                    type="monotone" 
                    dataKey="x" 
                    stroke="#06b6d4" 
                    strokeWidth={1.5} 
                    dot={false} 
                    isAnimationActive={false} 
                    name="CV_x(t)" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="y" 
                    stroke="#c084fc" 
                    strokeWidth={1.5} 
                    dot={false} 
                    isAnimationActive={false} 
                    name="CV_y(t)" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Real-time 2D Dynamics Metric Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Pos (x, y)</span>
              <span className="font-mono text-sm font-bold text-cyan-400">({walkerPos.x.toFixed(2)}, {walkerPos.y.toFixed(2)})</span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">PES V(x, y)</span>
              <span className="font-mono text-sm font-bold text-slate-200">{currentPES.toFixed(3)} <span className="text-[10px] text-slate-400">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Bias V<sub>B</sub>(x, y)</span>
              <span className="font-mono text-sm font-bold text-red-400">{currentBiasVal.toFixed(3)} <span className="text-[10px] text-slate-400">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Force Magnitude |F|</span>
              <span className="font-mono text-sm font-bold text-purple-400">{forceMag.toFixed(3)}</span>
            </div>
          </div>

        </div>
      </div>

      {/* Guide Modal */}
      {showGuideModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto relative">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen size={20} className="text-purple-400" />
                2D Metadynamics Simulation — Theory Guide
              </h3>
              <button onClick={() => setShowGuideModal(false)} className="text-slate-400 hover:text-white p-1 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="text-sm text-slate-300 space-y-4 leading-relaxed">
              <p>
                In <strong>2D Metadynamics</strong>, the walker particle diffuses over a two-dimensional energy landscape defined along two Collective Variables <MathInline tex="(s_1, s_2)" />.
              </p>

              {/* Section 1: 2D Langevin */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-2">
                <h4 className="font-bold text-purple-400 text-sm">1. 2D Overdamped Langevin Dynamics</h4>
                <p className="text-xs text-slate-400">Each coordinate evolves independently under the gradient of the total potential:</p>
                <MathBlock tex="\begin{aligned} dx &= -\frac{\partial}{\partial x}\bigl[V(x,y)+V_{\!B}(x,y,t)\bigr]\,dt + \sqrt{2k_{\!B}T\,dt}\;\eta_x \\\\ dy &= -\frac{\partial}{\partial y}\bigl[V(x,y)+V_{\!B}(x,y,t)\bigr]\,dt + \sqrt{2k_{\!B}T\,dt}\;\eta_y \end{aligned}" />
                <p className="text-xs text-slate-400">where <MathInline tex="\eta_x, \eta_y \sim \mathcal{N}(0,1)" /> are independent Gaussian noise terms.</p>
              </div>

              {/* Section 2: 2D Gaussian bias */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-3">
                <h4 className="font-bold text-cyan-400 text-sm">2. 2D Gaussian Bias Deposition</h4>
                <p className="text-xs text-slate-400">
                  2D Gaussian hills are deposited every <MathInline tex="\tau" /> steps at the current walker location <MathInline tex="(x(t'),\,y(t'))" />:
                </p>
                <MathBlock tex="V_{\!B}(x,y,t)=\sum_{t'<t}W(t')\,\exp\!\left(-\frac{(x-x(t'))^2+(y-y(t'))^2}{2\sigma^2}\right)" />

                <div className="space-y-2">
                  <div className="rounded-lg border border-slate-700/60 bg-slate-900/60 p-3">
                    <p className="text-xs font-bold text-slate-200 mb-1">Standard Metadynamics</p>
                    <p className="text-xs text-slate-400 mb-1">Constant hill height <MathInline tex="W(t')=W_0" />:</p>
                    <MathBlock tex="F(x,y) = -V_{\!B}(x,y,\,t\to\infty)" />
                  </div>
                  <div className="rounded-lg border border-indigo-700/40 bg-indigo-950/20 p-3">
                    <p className="text-xs font-bold text-indigo-300 mb-1">Well-Tempered Metadynamics (WT-MetaD)</p>
                    <p className="text-xs text-slate-400 mb-1">Hill height rescaled by accumulated bias:</p>
                    <MathBlock tex="W(t')=W_0\exp\!\left(-\frac{V_{\!B}(x(t'),y(t'),t')}{\Delta T}\right),\quad \Delta T=T(\gamma-1)" />
                    <p className="text-xs text-slate-400 mb-1">Free energy surface reconstruction:</p>
                    <MathBlock tex="F(x,y)=-\frac{\gamma}{\gamma-1}\,V_{\!B}(x,y,\,t\to\infty)" />
                  </div>
                </div>
              </div>

              {/* Section 3: Custom functions */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-2">
                <h4 className="font-bold text-emerald-400 text-sm">3. Custom 2D Energy Surfaces <MathInline tex="V(x,y)" /></h4>
                <p className="text-xs text-slate-400">Define 2D potential functions combining both variables, for example:</p>
                <div className="font-mono text-[11px] text-emerald-300 bg-slate-900 p-2.5 rounded-lg border border-slate-700/60 space-y-1">
                  <div>0.2*(x^2-4)^2 + 0.2*(y^2-4)^2</div>
                  <div>2*(cos(x)+cos(y)) + 0.1*(x^4+y^4)</div>
                  <div>sin(x)*cos(y) + 0.05*(x^2+y^2)</div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button onClick={() => setShowGuideModal(false)} className="py-2 px-5 bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-bold text-xs rounded-xl shadow-md">
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default MetadynamicsLab2D;
