#!/usr/bin/env bash
set -e

PROJECT_NAME="${1:-metadynamics_laboratory}"

echo "=== Creating Vite + React project in ./$PROJECT_NAME ==="

npm create vite@latest "$PROJECT_NAME" -- --template react

cd "$PROJECT_NAME"

echo "=== Installing dependencies ==="
npm install

echo "=== Installing recharts and lucide-react ==="
npm install recharts lucide-react

echo "=== Installing Tailwind v3, PostCSS and Autoprefixer ==="
npm install -D tailwindcss@3 postcss autoprefixer

echo "=== Initializing Tailwind CSS ==="
npx tailwindcss init -p

echo "=== Configuring folder structure ==="
mkdir -p src

echo "=== Writing tailwind.config.js ==="
cat << 'EOF' > tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

EOF

echo "=== Writing postcss.config.js ==="
cat << 'EOF' > postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

EOF

echo "=== Writing src/index.css ==="
cat << 'EOF' > src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }
  code, pre, .font-mono {
    font-family: 'JetBrains Mono', monospace;
  }
}

/* Custom Sleek Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.6);
}
::-webkit-scrollbar-thumb {
  background: rgba(51, 65, 85, 0.8);
  border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 1);
}

EOF

echo "=== Writing src/main.jsx ==="
cat << 'EOF' > src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

EOF

echo "=== Writing src/MathEq.jsx ==="
cat << 'EOF' > src/MathEq.jsx
/**
 * MathEq.jsx — Lightweight KaTeX wrapper for rendering LaTeX math in React.
 * Usage:
 *   <MathBlock tex="\frac{dx}{dt} = -\nabla V" />   ← display (centered)
 *   <MathInline tex="\sigma" />                      ← inline
 */
import React from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

function render(tex, displayMode) {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      trust: false,
      strict: false,
    });
  } catch {
    return `<span style="color:#f87171">[LaTeX error]</span>`;
  }
}

export function MathBlock({ tex, className = "" }) {
  return (
    <div
      className={"overflow-x-auto py-1 " + className}
      dangerouslySetInnerHTML={{ __html: render(tex, true) }}
    />
  );
}

export function MathInline({ tex }) {
  return (
    <span dangerouslySetInnerHTML={{ __html: render(tex, false) }} />
  );
}

EOF

echo "=== Writing src/MetadynamicsLab.jsx ==="
cat << 'EOF' > src/MetadynamicsLab.jsx
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { MathBlock, MathInline } from './MathEq';
import { 
  Play, Pause, RotateCcw, Activity, TrendingUp, Layers, Plus, Trash2, 
  Crosshair, BookOpen, Thermometer, Save, Upload, Hash, Calculator, 
  Sparkles, Gauge, Zap, Check, HelpCircle, X, Sliders, RefreshCw 
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ReferenceDot, Area, Legend 
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

// --- Box-Muller Transform for Normal Gaussian Distribution N(0, 1) ---
function gaussianRandom(rng) {
  let u1 = rng();
  let u2 = rng();
  while (u1 === 0) u1 = rng();
  return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
}

// --- Preset Mathematical Potential Energy Functions ---
const MATH_PRESETS = [
  { label: 'Symmetric Double Well', expr: '0.5 * (x^2 - 4)^2' },
  { label: 'Asymmetric Double Well', expr: '0.25 * x^4 - 2 * x^2 + 0.8 * x' },
  { label: 'Triple Energy Well', expr: '0.1 * x^6 - 2 * x^4 + 8 * x^2' },
  { label: 'Sinusoidal Wavy Surface', expr: '3 * cos(2 * x) + 0.15 * x^4' },
  { label: 'Harmonic Oscillator', expr: '1.5 * x^2' }
];

// --- Safe Recursive Math Expression Parser for V(x) ---
const parseAndEvalMath = (expr, x) => {
  if (!expr || typeof expr !== 'string') return 0;
  try {
    let str = expr.toLowerCase().trim();
    if (!str) return 0;

    // Implicit multiplication handling (e.g., 2x -> 2*x, 3(x) -> 3*(x))
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

// --- Physics: Potential Energy Surface V(x) ---
const getPES = (x, currentWells, pesMode = 'wells', pesFunctionStr = '') => {
  if (pesMode === 'function' && pesFunctionStr.trim()) {
    return parseAndEvalMath(pesFunctionStr, x);
  }
  let energy = 0;
  energy += 0.2 * Math.pow(x, 4); // Soft boundary walls
  currentWells.forEach(well => {
    energy += -well.depth * Math.exp(-Math.pow(x - well.pos, 2) / well.width);
  });
  return energy;
};

// --- Physics: Accumulated Bias Potential V_B(x) ---
const getBias = (x, storedBiases) => {
  let bias = 0;
  for (let g of storedBiases) {
    bias += g.h * Math.exp(-Math.pow(x - g.mu, 2) / (2 * g.sigma * g.sigma));
  }
  return bias;
};

// --- Physics: Conservative Forces -dV/dx ---
const getForce = (x, currentBias, currentWells, pesMode = 'wells', pesFunctionStr = '') => {
  const dx = 0.001;
  const dV_pes = (getPES(x + dx, currentWells, pesMode, pesFunctionStr) - getPES(x - dx, currentWells, pesMode, pesFunctionStr)) / (2 * dx);
  let dV_bias = 0;
  for (let g of currentBias) {
    const expo = Math.exp(-Math.pow(x - g.mu, 2) / (2 * g.sigma * g.sigma));
    dV_bias += g.h * expo * (-(x - g.mu) / (g.sigma * g.sigma));
  }
  return -(dV_pes + dV_bias);
};

// --- Custom Recharts Tooltip with Professional Readouts ---
const CustomGraphTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 backdrop-blur-md border border-slate-700/80 p-3.5 rounded-xl shadow-2xl text-xs space-y-1.5 min-w-[200px]">
        <div className="font-mono font-bold text-cyan-400 border-b border-slate-800 pb-1 flex justify-between">
          <span>Collective Variable (CV)</span>
          <span>x = {Number(label).toFixed(2)}</span>
        </div>
        {payload.map((entry, index) => (
          <div key={`item-${index}`} className="flex justify-between items-center text-slate-300">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: entry.color }}></span>
              {entry.name}:
            </span>
            <span className="font-mono font-semibold text-slate-100">
              {Number(entry.value).toFixed(3)} <span className="text-[10px] text-slate-400">kJ/mol</span>
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const MetadynamicsLab = () => {
  // --- Simulation Configuration States ---
  const [isRunning, setIsRunning] = useState(false);
  const [timeStep, setTimeStep] = useState(0);
  const [showGuideModal, setShowGuideModal] = useState(false);
  
  // Potential Energy Surface Mode & Function
  const [pesMode, setPesMode] = useState('wells'); // 'wells' | 'function'
  const [pesFunctionStr, setPesFunctionStr] = useState('0.5 * (x^2 - 4)^2');

  // Gaussian Wells Configuration
  const [wells, setWells] = useState([
    { id: 1, pos: -2, depth: 8, width: 0.8 },
    { id: 2, pos: 2, depth: 8, width: 0.8 }
  ]);

  // Metadynamics Hyperparameters
  const [gaussianHeight, setGaussianHeight] = useState(0.5); 
  const [gaussianWidth, setGaussianWidth] = useState(0.4);   
  const [depositionStride, setDepositionStride] = useState(20); 
  const [temperature, setTemperature] = useState(0.8); 

  // Well-Tempered Parameters
  const [isWellTempered, setIsWellTempered] = useState(false);
  const [biasFactor, setBiasFactor] = useState(10); // Gamma factor

  // Walker Simulation State
  const [walkerPos, setWalkerPos] = useState(-2); 
  const [biasPotentials, setBiasPotentials] = useState([]); 
  const [currentDepositionHeight, setCurrentDepositionHeight] = useState(0.5); 
  const [colvarHistory, setColvarHistory] = useState([{ step: 0, x: -2 }]);
  
  // Seed & PRNG State
  const [seed, setSeed] = useState(12345);
  const [useFixedSeed, setUseFixedSeed] = useState(false);
  const rngRef = useRef(Math.random);

  const savedCallback = useRef();
  const fileInputRef = useRef(null);

  const initRNG = (currentSeed) => {
    rngRef.current = mulberry32(currentSeed);
  };

  // --- Session Export / Import ---
  const handleExport = () => {
    const data = {
      version: "2.0",
      pesMode,
      pesFunctionStr,
      wells,
      biasPotentials,
      walkerPos,
      timeStep,
      colvarHistory,
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
    link.download = `metadynamics_session_${new Date().toISOString().slice(0,10)}.json`;
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
        setWalkerPos(data.walkerPos ?? -2);
        setTimeStep(data.timeStep || 0);
        if (data.colvarHistory) setColvarHistory(data.colvarHistory);
        
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
        alert("Invalid JSON session file format. Please load a valid session JSON generated by Metadynamics Lab.");
      }
    };
    reader.readAsText(file);
    e.target.value = null; 
  };

  // --- Gaussian Well Management ---
  const addWell = () => {
    const newId = wells.length > 0 ? Math.max(...wells.map(w => w.id)) + 1 : 1;
    setWells([...wells, { id: newId, pos: 0, depth: 6, width: 0.8 }]);
    handleReset();
  };

  const removeWell = (id) => {
    setWells(wells.filter(w => w.id !== id));
    handleReset();
  };

  const updateWell = (id, field, value) => {
    setWells(wells.map(w => w.id === id ? { ...w, [field]: parseFloat(value) } : w));
  };

  // --- Langevin Integration Step ---
  const stepSimulation = () => {
    let nextX = walkerPos;

    setWalkerPos((prevX) => {
      let force = getForce(prevX, biasPotentials, wells, pesMode, pesFunctionStr);
      const dt = 0.05;

      const MAX_FORCE = 15; 
      if (force > MAX_FORCE) force = MAX_FORCE;
      if (force < -MAX_FORCE) force = -MAX_FORCE;
      
      const gNoise = gaussianRandom(rngRef.current); 
      const noise = Math.sqrt(2 * temperature * dt) * gNoise;
      
      let newX = prevX + force * dt + noise;
      if (newX > 4.5) newX = 4.5;
      if (newX < -4.5) newX = -4.5;
      nextX = newX;
      return newX;
    });

    setTimeStep((prevTime) => {
      const nextTime = prevTime + 1;
      setColvarHistory(prev => [...prev.slice(-2000), { step: nextTime, x: parseFloat(nextX.toFixed(3)) }]);

      if (nextTime % depositionStride === 0) {
        let newHeight = gaussianHeight;

        if (isWellTempered) {
          const currentBiasV = getBias(nextX, biasPotentials);
          const deltaT = temperature * (biasFactor - 1);
          if (deltaT > 0) {
            newHeight = gaussianHeight * Math.exp(-currentBiasV / deltaT);
          }
        }
        
        setCurrentDepositionHeight(newHeight);

        setBiasPotentials(prevBias => [
          ...prevBias,
          { mu: nextX, h: newHeight, sigma: gaussianWidth }
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
        if (savedCallback.current) {
          savedCallback.current();
        }
      };
      const id = setInterval(tick, 50); 
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

    const startPos = pesMode === 'wells' ? (wells.length > 0 ? wells[0].pos : 0) : 0;
    setWalkerPos(startPos);
    setColvarHistory([{ step: 0, x: startPos }]);
  };

  const generateNewSeed = () => {
    const array = new Uint32Array(1);
    crypto.getRandomValues(array);
    const newSeed = array[0] % 1000000;
    setSeed(newSeed);
    setUseFixedSeed(true);
    initRNG(newSeed);
    setIsRunning(false);
    setTimeStep(0);
    setBiasPotentials([]);
    setCurrentDepositionHeight(gaussianHeight);
    const startPos = pesMode === 'wells' ? (wells.length > 0 ? wells[0].pos : 0) : 0;
    setWalkerPos(startPos);
  };

  useEffect(() => {
    initRNG(seed);
  }, [seed]);

  // --- Graph Grid & Data Calculations ---
  const xGrid = useMemo(() => {
    const points = [];
    for (let x = -4.5; x <= 4.5; x += 0.1) {
      points.push(parseFloat(x.toFixed(1)));
    }
    return points;
  }, []);

  const chartData = useMemo(() => {
    return xGrid.map(x => {
      const pes = getPES(x, wells, pesMode, pesFunctionStr);
      const bias = getBias(x, biasPotentials);
      
      let fesEst = -bias;
      if (isWellTempered && biasFactor > 1) {
        const factor = biasFactor / (biasFactor - 1);
        fesEst = -factor * bias;
      }

      return {
        x: x,
        PES: pes,
        BiasOnly: bias, 
        Total: pes + bias,
        FES_Est: fesEst 
      };
    });
  }, [xGrid, wells, biasPotentials, isWellTempered, biasFactor, pesMode, pesFunctionStr]);

  const yDomain = useMemo(() => {
    let min = -10;
    if (pesMode === 'wells' && wells.length > 0) {
      const maxDepth = Math.max(...wells.map(w => w.depth));
      min = -(maxDepth + 5); 
    } else if (pesMode === 'function') {
      let minVal = 0;
      for (let x = -4.5; x <= 4.5; x += 0.5) {
        const v = parseAndEvalMath(pesFunctionStr, x);
        if (v < minVal) minVal = v;
      }
      min = Math.min(-10, Math.floor(minVal - 2));
    }
    return [min, 'auto'];
  }, [wells, pesMode, pesFunctionStr]);

  // Current Instantaneous Metrics
  const currentPES = getPES(walkerPos, wells, pesMode, pesFunctionStr);
  const currentBiasVal = getBias(walkerPos, biasPotentials);
  const currentForce = getForce(walkerPos, biasPotentials, wells, pesMode, pesFunctionStr);

  return (
    <div className="flex flex-col w-full space-y-3">
      
      {/* Top Header Card */}
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-3 relative overflow-hidden">
        <div className="flex items-center gap-4 z-10">
          <div className="p-3 bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 rounded-xl text-cyan-400 shadow-lg shadow-cyan-500/10">
            <Activity size={28} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Metadynamics Simulation Lab
              </h1>
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-cyan-950 text-cyan-400 border border-cyan-800/60 rounded-full">
                v2.0 • Box-Muller WT-Engine
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              Interactive 1D Langevin Dynamics & Free Energy Surface (FES) Reconstruction
            </p>
          </div>
        </div>

        {/* Real-time Status Badges & Action Controls */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end z-10">
          
          {/* Quick Metrics */}
          <div className="hidden sm:flex items-center gap-2 mr-2 bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800/80 text-xs">
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-white uppercase font-semibold">Steps</span>
              <span className="font-mono font-bold text-white">{timeStep}</span>
            </div>
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-white uppercase font-semibold">Hills</span>
              <span className="font-mono font-bold text-cyan-400">{biasPotentials.length}</span>
            </div>
            <div className="flex flex-col items-center px-2">
              <span className="text-[10px] text-white uppercase font-semibold">Height W(t)</span>
              <span className={`font-mono font-bold ${isWellTempered && currentDepositionHeight < 0.05 ? 'text-amber-400' : 'text-white'}`}>
                {currentDepositionHeight.toFixed(3)}
              </span>
            </div>
          </div>

          {/* Session File IO */}
          <div className="flex items-center gap-1.5 bg-slate-950/60 p-1 rounded-xl border border-slate-800">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleImport} 
              accept=".json" 
              className="hidden" 
            />
            <button 
              onClick={handleExport}
              className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/60 rounded-lg transition-colors"
              title="Save Session (JSON)"
            >
              <Save size={18} />
            </button>
            <button 
              onClick={() => fileInputRef.current.click()}
              className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/60 rounded-lg transition-colors"
              title="Load Session (JSON)"
            >
              <Upload size={18} />
            </button>
          </div>

          {/* Guide & Documentation */}
          <button
            onClick={() => setShowGuideModal(true)}
            className="py-2 px-3.5 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
          >
            <BookOpen size={16} className="text-cyan-400" />
            <span>Guide</span>
          </button>

          {/* Reset Control */}
          <button
            onClick={handleReset}
            className="p-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 rounded-xl transition-all shadow-sm"
            title="Reset Simulation"
          >
            <RotateCcw size={18} />
          </button>

          {/* Simulation Play / Pause Button */}
          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`py-2.5 px-6 rounded-xl font-bold text-xs tracking-wide shadow-lg flex items-center gap-2 transition-all ${
              isRunning 
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-amber-500/20 hover:from-amber-400 hover:to-amber-500' 
                : 'bg-gradient-to-r from-emerald-500 to-teal-600 text-slate-950 shadow-emerald-500/20 hover:from-emerald-400 hover:to-teal-500'
            }`}
          >
            {isRunning ? <><Pause size={18} /> PAUSE</> : <><Play size={18} /> SIMULATE</>}
          </button>
        </div>
      </header>

      {/* Main Grid: Control Panel + Simulation Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          
          {/* Card 1: Potential Energy Surface (PES) Configuration */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="flex justify-between items-center pb-2.5 border-b border-slate-800/80">
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Crosshair size={16} className="text-cyan-400" />
                Potential Surface (PES)
              </h3>
              
              {/* PES Mode Selector Tabs */}
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                <button
                  onClick={() => { setPesMode('wells'); handleReset(); }}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    pesMode === 'wells' 
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-sm' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Gaussian Wells
                </button>
                <button
                  onClick={() => { setPesMode('function'); handleReset(); }}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    pesMode === 'function' 
                      ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-sm' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Math V(x)
                </button>
              </div>
            </div>

            {pesMode === 'wells' ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">Defined Potential Wells</span>
                  <button 
                    onClick={addWell} 
                    className="text-xs bg-cyan-950 text-cyan-400 hover:bg-cyan-900/60 border border-cyan-800/50 px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold transition-colors"
                  >
                    <Plus size={14} /> Add Well
                  </button>
                </div>
                <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                  {wells.map((well, idx) => (
                    <div key={well.id} className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-cyan-400"></span> Well #{idx + 1}
                        </span>
                        <button onClick={() => removeWell(well.id)} className="text-slate-500 hover:text-red-400 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-xs text-slate-400">
                        <div>
                          <div className="flex justify-between mb-1">
                            <span>Position</span>
                            <span className="font-mono text-cyan-400">{well.pos}</span>
                          </div>
                          <input type="range" min="-3.5" max="3.5" step="0.1" value={well.pos} onChange={(e) => updateWell(well.id, 'pos', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"/>
                        </div>
                        <div>
                          <div className="flex justify-between mb-1">
                            <span>Depth</span>
                            <span className="font-mono text-indigo-400">{well.depth}</span>
                          </div>
                          <input type="range" min="1" max="15" step="0.5" value={well.depth} onChange={(e) => updateWell(well.id, 'depth', e.target.value)} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-400"/>
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
                    <Calculator size={14} className="text-cyan-400" /> Expression V(x):
                  </label>
                  <div className="relative">
                    <input 
                      type="text" 
                      value={pesFunctionStr} 
                      onChange={(e) => { 
                        setPesFunctionStr(e.target.value); 
                        handleReset(); 
                      }} 
                      placeholder="e.g. 0.5 * (x^2 - 4)^2" 
                      className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-mono text-cyan-300 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 outline-none shadow-inner"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">Load Preset Function:</label>
                  <select 
                    onChange={(e) => { 
                      if (e.target.value) {
                        setPesFunctionStr(e.target.value); 
                        handleReset();
                      }
                    }}
                    value={pesFunctionStr}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:ring-2 focus:ring-cyan-500/50 outline-none"
                  >
                    {MATH_PRESETS.map((preset, idx) => (
                      <option key={idx} value={preset.expr}>{preset.label} — {preset.expr}</option>
                    ))}
                  </select>
                </div>

                <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                  <span className="font-semibold text-slate-300 block">Supported Syntax:</span>
                  <div className="font-mono text-[10px] text-slate-400 leading-relaxed">
                    + - * / ^ | sin(x) cos(x) tan(x) exp(x) log(x) sqrt(x) abs(x) | pi e
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Card 2: Metadynamics & Hyperparameters */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="pb-2 border-b border-slate-800/80 font-semibold text-xs text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Layers size={16} className="text-cyan-400" />
              Metadynamics Parameters
            </div>
            
            <div className="space-y-4">
              
              {/* Well-Tempered Metadynamics Toggle */}
              <div className="bg-gradient-to-br from-slate-950 to-indigo-950/30 p-3.5 rounded-xl border border-indigo-900/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                    <Thermometer size={16} className="text-indigo-400" /> Well-Tempered MetaD
                  </span>
                  <div 
                    className={`w-10 h-5 rounded-full cursor-pointer relative transition-colors ${isWellTempered ? 'bg-indigo-600' : 'bg-slate-800'}`}
                    onClick={() => { setIsWellTempered(!isWellTempered); handleReset(); }}
                  >
                    <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-all shadow-md ${isWellTempered ? 'left-5.5' : 'left-0.5'}`}></div>
                  </div>
                </div>

                {isWellTempered && (
                  <div className="mt-3.5 pt-3 border-t border-indigo-900/40 space-y-2">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span>Bias Factor (γ)</span>
                      <span className="font-mono font-bold text-indigo-400">{biasFactor}</span>
                    </div>
                    <input 
                      type="range" min="2" max="30" step="1" 
                      value={biasFactor} 
                      onChange={(e) => { setBiasFactor(parseInt(e.target.value)); handleReset(); }} 
                      className="w-full h-1.5 bg-indigo-900/60 rounded-lg appearance-none cursor-pointer accent-indigo-400"
                    />
                  </div>
                )}
              </div>

              {/* Initial Hill Height (W0) */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Initial Hill Height (W₀)</span>
                  <span className="font-mono font-semibold text-cyan-400">{gaussianHeight.toFixed(2)} <span className="text-[10px] text-slate-500">kJ/mol</span></span>
                </div>
                <input type="range" min="0.1" max="2.0" step="0.1" value={gaussianHeight} onChange={(e) => setGaussianHeight(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"/>
              </div>

              {/* Hill Width (Sigma) */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Gaussian Width (σ)</span>
                  <span className="font-mono font-semibold text-purple-400">{gaussianWidth.toFixed(2)}</span>
                </div>
                <input type="range" min="0.1" max="1.0" step="0.05" value={gaussianWidth} onChange={(e) => setGaussianWidth(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"/>
              </div>

              {/* Temperature (T) */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Thermal Energy (k<sub>B</sub>T)</span>
                  <span className="font-mono font-semibold text-amber-400">{temperature.toFixed(2)}</span>
                </div>
                <input type="range" min="0.1" max="3.0" step="0.1" value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"/>
              </div>

              {/* Stride */}
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Deposition Stride (τ)</span>
                  <span className="font-mono font-semibold text-emerald-400">{depositionStride} <span className="text-[10px] text-slate-500">steps</span></span>
                </div>
                <input type="range" min="5" max="50" step="5" value={depositionStride} onChange={(e) => setDepositionStride(parseInt(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"/>
              </div>

            </div>
          </div>

          {/* Card 3: Reproducibility & RNG Seed */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-xl space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800 text-xs text-slate-400 font-semibold uppercase tracking-wider">
              <span className="flex items-center gap-1.5"><Hash size={14} className="text-cyan-400" /> Reproducibility</span>
              <button 
                onClick={generateNewSeed}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-mono font-normal"
                title="Generate new random seed"
              >
                <RefreshCw size={12} /> New Seed
              </button>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="block text-[11px] text-slate-400 mb-1 font-medium">RNG Seed</label>
                <input 
                  type="number" 
                  value={seed} 
                  onChange={(e) => { 
                    const s = parseInt(e.target.value) || 0;
                    setSeed(s); 
                    setUseFixedSeed(true);
                    setIsRunning(false);
                    initRNG(s);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-xs font-mono text-center text-slate-200"
                />
              </div>
              <div className="flex items-center gap-2 pt-4">
                <input 
                  type="checkbox" 
                  id="fixedSeedCheck" 
                  checked={useFixedSeed} 
                  onChange={(e) => setUseFixedSeed(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-cyan-500 cursor-pointer"
                />
                <label htmlFor="fixedSeedCheck" className="text-xs text-slate-300 cursor-pointer select-none">
                  Fixed Seed
                </label>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Interactive Stage & Graphs (8 cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          
          {/* Main Stage Chart Container */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-2xl flex flex-col h-[415px] relative">
            <div className="flex justify-between items-center mb-1">
              <div>
                <h3 className="font-bold text-slate-100 flex items-center gap-2 text-sm">
                  <TrendingUp size={16} className="text-cyan-400" /> 
                  Real-Time Dynamics & FES Reconstruction
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                  isWellTempered 
                    ? 'bg-indigo-950/80 text-indigo-300 border-indigo-800/80' 
                    : 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
                }`}>
                  {isWellTempered ? `WT-MetaD (γ = ${biasFactor})` : 'Standard MetaD'}
                </span>
              </div>
            </div>

            {/* Recharts Canvas */}
            <div className="flex-1 w-full min-h-[330px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 25, left: 15, bottom: 25 }}>
                  <defs>
                    <linearGradient id="biasGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                  <XAxis 
                    dataKey="x" 
                    type="number" 
                    domain={[-4.5, 4.5]} 
                    stroke="#94a3b8" 
                    fontSize={10}
                    tickCount={10}
                    label={{ value: 'Collective Variable (CV)', position: 'bottom', offset: 10, fill: '#94a3b8', fontSize: 11 }} 
                  />
                  <YAxis 
                    domain={yDomain} 
                    stroke="#94a3b8" 
                    fontSize={10}
                    label={{ value: 'Energy (kJ/mol)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 11 }} 
                  />
                  <Tooltip content={<CustomGraphTooltip />} />
                  <Legend verticalAlign="top" height={28} wrapperStyle={{ paddingBottom: '5px', fontSize: '11px' }}/>
                  
                  {/* Accumulated Bias Area */}
                  <Area 
                    type="monotone" 
                    dataKey="BiasOnly" 
                    stroke="none" 
                    fill="url(#biasGradient)" 
                    isAnimationActive={false} 
                    name="Accumulated Bias V_B(x)" 
                  />

                  {/* PES Curve */}
                  <Line 
                    type="monotone" 
                    dataKey="PES" 
                    stroke="#38bdf8" 
                    strokeWidth={2.5} 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Original PES V(x)" 
                  />

                  {/* Total Potential Curve */}
                  <Line 
                    type="monotone" 
                    dataKey="Total" 
                    stroke="#34d399" 
                    strokeWidth={2} 
                    strokeDasharray="5 5" 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Total Potential V + V_B" 
                  />
                  
                  {/* Reconstructed FES Curve */}
                  <Line 
                    type="monotone" 
                    dataKey="FES_Est" 
                    stroke="#c084fc" 
                    strokeWidth={2} 
                    strokeDasharray="8 4" 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Estimated FES F(x)" 
                  />
                  
                  {/* Walker Particle Reference Dot */}
                  <ReferenceDot 
                    x={walkerPos} 
                    y={currentPES + currentBiasVal} 
                    r={6} 
                    fill="#06b6d4" 
                    stroke="#ffffff" 
                    strokeWidth={2} 
                    isAnimationActive={false} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* COLVAR Time-Series Chart Card */}
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-3 shadow-xl space-y-1">
            <div className="flex justify-between items-center pb-1 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-slate-100 flex items-center gap-2 text-xs">
                  <Activity size={14} className="text-cyan-400" />
                  COLVAR Time-Series Trajectory: x(t)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded-lg border border-slate-800 font-bold">
                CV x = {walkerPos.toFixed(3)}
              </span>
            </div>

            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={colvarHistory} margin={{ top: 5, right: 20, left: 15, bottom: 22 }}>
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
                    label={{ value: 'CV x(t)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 10 }} 
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', fontSize: '11px', padding: '6px 10px' }} 
                    labelStyle={{ color: '#38bdf8', fontWeight: 'bold' }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="x" 
                    stroke="#06b6d4" 
                    strokeWidth={1.5} 
                    dot={false} 
                    isAnimationActive={false} 
                    name="CV x(t)" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Real-time Dynamics Metric Cards Below Chart */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Walker Pos (x)</span>
              <span className="font-mono text-sm font-bold text-cyan-400">{walkerPos.toFixed(3)}</span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">PES Energy V(x)</span>
              <span className="font-mono text-sm font-bold text-slate-200">{currentPES.toFixed(3)} <span className="text-[10px] text-slate-400">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Bias Energy V<sub>B</sub>(x)</span>
              <span className="font-mono text-sm font-bold text-red-400">{currentBiasVal.toFixed(3)} <span className="text-[10px] text-slate-400">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-2 shadow-lg">
              <span className="text-[10px] text-white uppercase font-semibold block">Net Force (-∇V)</span>
              <span className="font-mono text-sm font-bold text-emerald-400">{currentForce.toFixed(3)}</span>
            </div>
          </div>

        </div>
        {/* Guide & Scientific Theory Modal */}
      {showGuideModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto relative">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen size={20} className="text-cyan-400" />
                Metadynamics Simulation — Theory Guide
              </h3>
              <button onClick={() => setShowGuideModal(false)} className="text-slate-400 hover:text-white p-1 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="text-sm text-slate-300 space-y-4 leading-relaxed">
              <p>
                <strong>Metadynamics</strong> is a powerful enhanced sampling technique in computational physics and chemistry designed to accelerate rare events and reconstruct Free Energy Surfaces (FES) along chosen Collective Variables (CVs).
              </p>

              {/* Section 1 */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-2">
                <h4 className="font-bold text-cyan-400 text-sm">1. Overdamped Langevin (Brownian) Dynamics</h4>
                <p className="text-xs text-slate-400">
                  The particle position <MathInline tex="x(t)" /> evolves under thermal fluctuations according to:
                </p>
                <MathBlock tex="dx = -\nabla\bigl[V(x) + V_{\!B}(x,\,t)\bigr]\,dt + \sqrt{2\,k_{\!B}T\,dt}\;\eta(t)" />
                <p className="text-xs text-slate-400">
                  where <MathInline tex="\eta(t)\sim\mathcal{N}(0,1)" /> is standard Gaussian noise generated via the Box–Muller transform.
                </p>
              </div>

              {/* Section 2 */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-3">
                <h4 className="font-bold text-indigo-400 text-sm">2. Bias Potential — Gaussian Hill Deposition</h4>
                <p className="text-xs text-slate-400">
                  Gaussian hills of height <MathInline tex="W_0" /> and width <MathInline tex="\sigma" /> are deposited every <MathInline tex="\tau" /> steps at the current walker position:
                </p>
                <MathBlock tex="V_{\!B}(x,\,t) = \sum_{t'=\tau,2\tau,\ldots}^{t'<t} W(t')\,\exp\!\left(-\frac{(x - x(t'))^2}{2\sigma^2}\right)" />

                <div className="space-y-2">
                  <div className="rounded-lg border border-slate-700/60 bg-slate-900/60 p-3">
                    <p className="text-xs font-bold text-slate-200 mb-1">Standard Metadynamics</p>
                    <p className="text-xs text-slate-400 mb-1">Constant hill height <MathInline tex="W(t') = W_0" />. Free energy estimated as:</p>
                    <MathBlock tex="F(x) = -V_{\!B}(x,\,t\to\infty)" />
                  </div>
                  <div className="rounded-lg border border-indigo-700/40 bg-indigo-950/20 p-3">
                    <p className="text-xs font-bold text-indigo-300 mb-1">Well-Tempered Metadynamics (WT-MetaD)</p>
                    <p className="text-xs text-slate-400 mb-1">Hill height decays as the bias fills the well:</p>
                    <MathBlock tex="W(t') = W_0\,\exp\!\left(-\frac{V_{\!B}(x(t'),\,t')}{\Delta T}\right),\quad \Delta T = T\,(\gamma-1)" />
                    <p className="text-xs text-slate-400 mb-1">where <MathInline tex="\gamma" /> is the bias factor. The FES is reconstructed as:</p>
                    <MathBlock tex="F(x) = -\frac{\gamma}{\gamma - 1}\,V_{\!B}(x,\,t\to\infty)" />
                  </div>
                </div>
              </div>

              {/* Section 3 */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-700/80 space-y-2">
                <h4 className="font-bold text-purple-400 text-sm">3. Custom Mathematical Energy Surfaces</h4>
                <p className="text-xs text-slate-400">
                  You can define custom energy surfaces <MathInline tex="V(x)" /> using arbitrary algebraic expressions evaluated at runtime, for example:
                </p>
                <div className="font-mono text-[11px] text-emerald-300 bg-slate-900 p-2.5 rounded-lg border border-slate-700/60 space-y-1">
                  <div>0.5*(x^2-4)^2</div>
                  <div>3*cos(2*x) + 0.15*x^4</div>
                  <div>sin(x)*exp(-0.1*x^2)</div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setShowGuideModal(false)}
                className="py-2 px-5 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs rounded-xl shadow-md"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
    </div>
  );
};

export default MetadynamicsLab;
EOF

echo "=== Writing src/MetadynamicsLab2D.jsx ==="
cat << 'EOF' > src/MetadynamicsLab2D.jsx
import React, { useState, useEffect, useRef } from 'react';
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

  // 1D Projections Mode (computed inside canvas useEffect)
  const [projMode, setProjMode] = useState('int'); // 'int' | 'min'

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
    ctx.strokeStyle = 'rgba(6, 182, 212, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx0, hy0); ctx.lineTo(hx1, hy0); ctx.stroke();

    // ── 6. Draw F(CV₂) — right strip ────────────────────────────
    const sR_lft = hx1 + 3;
    const sR_rgt = W - 4;
    const sR_W   = sR_rgt - sR_lft;

    ctx.fillStyle = 'rgba(2, 8, 23, 0.55)';
    ctx.fillRect(sR_lft, hy0, sR_W, hH);

    if (maxPY > 1e-6) {
      const pts2 = [];
      for (let gy = 0; gy < res; gy++) {
        pts2.push({
          py: hy0 + (gy + 0.5) * cH,
          px: sR_lft + (fProjY[gy] / maxPY) * (sR_W - 6)
        });
      }
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
    ctx.strokeStyle = 'rgba(192, 132, 252, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(hx1, hy0); ctx.lineTo(hx1, hy1); ctx.stroke();

    // ── 7. Axis ticks and labels ─────────────────────────────────
    const axisTicks = [-4.0, -2.0, 0, 2.0, 4.0];
    ctx.font = 'bold 10px Inter, monospace';

    for (const tx of axisTicks) {
      const cx = toHX(tx);
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.fillRect(cx - 0.5, hy1, 1, 5);
      ctx.fillStyle = 'rgba(203, 213, 225, 0.85)';
      ctx.textAlign = 'center';
      ctx.fillText(tx > 0 ? `+${tx.toFixed(1)}` : `${tx.toFixed(1)}`, cx, hy1 + 16);
    }

    for (const ty of axisTicks) {
      const cy = toHY(ty);
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.fillRect(hx0 - 5, cy - 0.5, 5, 1);
      ctx.fillStyle = 'rgba(203, 213, 225, 0.85)';
      ctx.textAlign = 'right';
      ctx.fillText(ty > 0 ? `+${ty.toFixed(1)}` : `${ty.toFixed(1)}`, hx0 - 7, cy + 4);
    }

    // CV₁ badge
    ctx.font = 'bold 11px Inter, monospace';
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.fillRect(hx1 - 74, hy1 - 24, 68, 20);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
    ctx.lineWidth = 1;
    ctx.strokeRect(hx1 - 74, hy1 - 24, 68, 20);
    ctx.fillStyle = '#38bdf8';
    ctx.textAlign = 'center';
    ctx.fillText('CV\u2081 (x)', hx1 - 40, hy1 - 10);

    // CV₂ badge
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

    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cpx = (e.clientX - rect.left) * scaleX;
    const cpy = (e.clientY - rect.top) * scaleY;

    const ML = 50, MB = 35, MT = 85, MR = 115;
    const hx0 = ML, hx1 = canvas.width - MR;
    const hy0 = MT, hy1 = canvas.height - MB;
    const hW = hx1 - hx0, hH = hy1 - hy0;

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

EOF

echo "=== Writing src/OPESSimulator.jsx ==="
cat << 'EOF' > src/OPESSimulator.jsx
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

EOF

echo "=== Writing src/OpesVisualizer.jsx ==="
cat << 'EOF' > src/OpesVisualizer.jsx
import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Upload,
  FileText,
  TrendingUp,
  Activity,
  Layers,
  Clock,
  Zap,
  Award,
  Sliders,
  RefreshCw,
  RotateCcw,
  Play,
  Pause,
  Download,
  ImageIcon,
  ZoomIn,
  X,
  BookOpen,
  HelpCircle,
  BarChart2,
  AlertTriangle
} from "lucide-react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea
} from "recharts";
import { MathBlock, MathInline } from "./MathEq";

// --- OPES Inspector Parameters Control Panel (Column 2) ---
function OpesControlPanel({
  energyRefMode,
  setEnergyRefMode,
  inputNumBins,
  setInputNumBins,
  inputCustomBias,
  setInputCustomBias,
  energyUnits,
  setEnergyUnits,
  inputGridMin,
  setInputGridMin,
  inputGridMax,
  setInputGridMax,
  handleApplyGridParams,
  handleResetGridBounds,
  opesMetadata
}) {
  return (
    <div className="flex flex-col space-y-4 font-sans text-slate-100">
      {/* Energy Display Mode Card */}
      <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 space-y-2.5 shadow-xl">
        <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-2">
          <Sliders size={14} className="text-amber-400" />
          Energy Display Mode
        </h3>

        <div className="space-y-2 text-xs">
          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Bulk Plateau Reference [F(bulk) = 0]</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Sets bulk solvent energy to 0, minimum well depth is -ΔG
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeOpes"
              checked={energyRefMode === "plateauZero"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("plateauZero")}
              className="accent-amber-500 mt-1"
            />
          </label>

          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Relative to Minimum [F(min) = 0]</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Sets minimum bound well to 0, bulk plateau is +ΔG
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeOpes"
              checked={energyRefMode === "minZero"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("minZero")}
              className="accent-amber-500 mt-1"
            />
          </label>

          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Direct Potential V(s)</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Direct cumulative OPES bias potential
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeOpes"
              checked={energyRefMode === "raw"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("raw")}
              className="accent-amber-500 mt-1"
            />
          </label>
        </div>
      </div>

      {/* OPES Grid Parameters Form */}
      <form onSubmit={handleApplyGridParams} className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 space-y-2.5 flex flex-col justify-between shadow-xl">
        <div>
          <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-2 mb-2">
            <Sliders size={14} className="text-amber-400" />
            OPES Grid Parameters
          </h3>

          <div className="flex flex-col space-y-2">
            <div>
              <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                Grid Resolution (Bins):
              </label>
              <input
                type="number"
                min="50"
                max="1000"
                value={inputNumBins}
                onChange={(e) => setInputNumBins && setInputNumBins(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-amber-300 font-mono focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                Bias Factor (γ):
              </label>
              <input
                type="text"
                placeholder={`Detected: ${opesMetadata?.biasFactor ?? 40}`}
                value={inputCustomBias}
                onChange={(e) => setInputCustomBias && setInputCustomBias(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-cyan-300 font-mono focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                Energy Units:
              </label>
              <select
                value={energyUnits}
                onChange={(e) => setEnergyUnits && setEnergyUnits(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none"
              >
                <option value="kJ/mol">kJ/mol</option>
                <option value="kcal/mol">kcal/mol</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-0.5">
              <div>
                <label className="block text-[9px] text-slate-400 mb-0.5 font-medium">Min CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMin}
                  onChange={(e) => setInputGridMin && setInputGridMin(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-[9px] text-slate-400 mb-0.5 font-medium">Max CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMax}
                  onChange={(e) => setInputGridMax && setInputGridMax(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-3">
          <button
            type="submit"
            className="flex-1 py-2 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-md"
          >
            <RefreshCw size={14} /> Apply Parameters
          </button>

          <button
            type="button"
            onClick={handleResetGridBounds}
            className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 rounded-xl text-xs font-semibold"
            title="Reset Bounds"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </form>
    </div>
  );
}

export default function OpesVisualizer() {
  const [opesData, setOpesData] = useState(null);
  const [fileName, setFileName] = useState("");
  const [fileType, setFileType] = useState(""); // "KERNELS" | "STATE"
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [activeTab, setActiveTab] = useState("fes"); // "fes" | "height" | "cv" | "theory"
  const [energyRefMode, setEnergyRefMode] = useState("plateauZero");
  const [energyUnits, setEnergyUnits] = useState("kJ/mol");

  const [inputNumBins, setInputNumBins] = useState("300");
  const [inputCustomBias, setInputCustomBias] = useState("");
  const [inputGridMin, setInputGridMin] = useState("");
  const [inputGridMax, setInputGridMax] = useState("");

  const [numBins, setNumBins] = useState(300);
  const [gridMinUser, setGridMinUser] = useState("");
  const [gridMaxUser, setGridMaxUser] = useState("");

  const [timeStepProgress, setTimeStepProgress] = useState(100);
  const [isPlayingTime, setIsPlayingTime] = useState(false);
  const fileInputRef = useRef(null);

  // Parse PLUMED OPES file (STATE Mandatory with internal 'zed' check)
  const parseOpesFile = (text, name) => {
    try {
      if (!text.includes("zed")) {
        setOpesData(null);
        throw new Error(
          "OPES_STATE is mandatory! The uploaded file is not a valid OPES_STATE file. Please upload a valid PLUMED OPES_STATE file."
        );
      }

      const lines = text.split("\n");
      let fields = [];
      let biasFactor = 40.0;
      let epsilon = 1e-18;
      let kernelCutoff = 9.0;
      let zed = 0.0;
      let sumWeights = 0.0;
      let counter = 0;
      let actionType = "OPES_METAD";

      const kernels = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        if (line.startsWith("#!")) {
          // Parse Header Directives
          if (line.includes("FIELDS")) {
            fields = line.replace("#! FIELDS", "").trim().split(/\s+/);
          } else if (line.includes("SET biasfactor")) {
            biasFactor = parseFloat(line.split(/\s+/).pop());
          } else if (line.includes("SET epsilon")) {
            epsilon = parseFloat(line.split(/\s+/).pop());
          } else if (line.includes("SET kernel_cutoff")) {
            kernelCutoff = parseFloat(line.split(/\s+/).pop());
          } else if (line.includes("SET zed")) {
            zed = parseFloat(line.split(/\s+/).pop());
          } else if (line.includes("SET sum_weights")) {
            sumWeights = parseFloat(line.split(/\s+/).pop());
          } else if (line.includes("SET counter")) {
            counter = parseInt(line.split(/\s+/).pop());
          } else if (line.includes("SET action")) {
            actionType = line.split(/\s+/).pop();
          }
          continue;
        }

        // Parse numerical row
        const tokens = line.split(/\s+/).map(Number);
        if (tokens.length >= 4 && !isNaN(tokens[0])) {
          // Default field index mapping
          let timeIdx = fields.indexOf("time");
          let zIdx = fields.indexOf("z");
          let sigmaIdx = fields.indexOf("sigma_z");
          let heightIdx = fields.indexOf("height");
          let logweightIdx = fields.indexOf("logweight");

          if (timeIdx === -1) timeIdx = 0;
          if (zIdx === -1) zIdx = 1;
          if (sigmaIdx === -1) sigmaIdx = 2;
          if (heightIdx === -1) heightIdx = 3;

          const time = tokens[timeIdx] ?? tokens[0];
          const z = tokens[zIdx] ?? tokens[1];
          const sigma = tokens[sigmaIdx] ?? tokens[2];
          const height = tokens[heightIdx] ?? tokens[3];
          const logweight = logweightIdx !== -1 ? tokens[logweightIdx] : undefined;

          kernels.push({
            idx: kernels.length + 1,
            time,
            z,
            sigma,
            height,
            logweight
          });
        }
      }

      if (kernels.length === 0) {
        throw new Error("No valid OPES data rows found in file.");
      }

      const detectedType = name.toUpperCase().includes("STATE") || zed > 0 ? "STATE" : "KERNELS";

      // Compute statistics
      const allZ = kernels.map((k) => k.z);
      const minZ = Math.min(...allZ);
      const maxZ = Math.max(...allZ);
      const totalTime = kernels[kernels.length - 1].time;

      setFileName(name);
      setFileType(detectedType);
      setOpesData({
        kernels,
        biasFactor,
        epsilon,
        kernelCutoff,
        zed,
        sumWeights,
        counter: counter || kernels.length,
        actionType,
        minZ,
        maxZ,
        totalTime,
        detectedType
      });
      setErrorMsg("");
    } catch (err) {
      setErrorMsg(err.message || "Failed to parse OPES file.");
    }
  };

  const [isDraggingFile, setIsDraggingFile] = useState(false);

  const processFileObj = (fileObj) => {
    if (!fileObj) return;
    setIsLoading(true);
    const reader = new FileReader();
    reader.onload = (event) => {
      parseOpesFile(event.target.result, fileObj.name);
      setIsLoading(false);
    };
    reader.onerror = () => {
      setErrorMsg("Error reading dropped file");
      setIsLoading(false);
    };
    reader.readAsText(fileObj);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) processFileObj(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDraggingFile) setIsDraggingFile(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDraggingFile(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFile(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      processFileObj(file);
    }
  };

  // ─── Pure FES computation (extracted so it can be called imperatively) ────
  const computeFrameData = useCallback((progress) => {
    if (!opesData || !opesData.kernels.length) return null;

    const maxIdx = Math.max(
      1,
      Math.floor((progress / 100) * opesData.kernels.length)
    );
    const activeKernels = opesData.kernels.slice(0, maxIdx);
    const sampleTime = activeKernels[activeKernels.length - 1].time;

    const effectiveGamma = parseFloat(inputCustomBias) || opesData.biasFactor || 40.0;
    const kB = energyUnits === "kcal/mol" ? 0.001987204 : 0.008314462;
    const kBT = kB * 300;

    const avgSigma = activeKernels.reduce((acc, k) => acc + k.sigma, 0) / activeKernels.length;
    const autoMin = Math.min(...activeKernels.map((k) => k.z)) - 3 * avgSigma;
    const autoMax = Math.max(...activeKernels.map((k) => k.z)) + 3 * avgSigma;

    const startZ = gridMinUser !== "" ? parseFloat(gridMinUser) : autoMin;
    const endZ   = gridMaxUser !== "" ? parseFloat(gridMaxUser) : autoMax;
    const bins    = numBins;
    const stepZ   = (endZ - startZ) / (bins - 1);

    const isStateFile = opesData.detectedType === "STATE" || activeKernels[0]?.logweight === undefined;

    const gridPoints = [];

    if (isStateFile) {
      const rawProbSums = new Float64Array(bins);
      let maxProb = 0;

      for (let i = 0; i < bins; i++) {
        const s = startZ + i * stepZ;
        let probSum = 0;
        for (let k = 0; k < activeKernels.length; k++) {
          const kern = activeKernels[k];
          const diff = s - kern.z;
          const arg = (diff * diff) / (2 * kern.sigma * kern.sigma);
          if (arg < 12.0) probSum += kern.height * Math.exp(-arg);
        }
        rawProbSums[i] = probSum;
        if (probSum > maxProb) maxProb = probSum;
      }

      for (let i = 0; i < bins; i++) {
        const s    = startZ + i * stepZ;
        const prob = rawProbSums[i];
        let fesVal = 0;
        if (prob > 0) {
          if (energyRefMode === "plateauZero") {
            fesVal = -kBT * Math.log(prob / (maxProb + 1e-12));
          } else if (energyRefMode === "minZero") {
            fesVal = kBT * Math.log((maxProb + 1e-12) / (prob + 1e-12));
          } else {
            fesVal = (1 - 1 / effectiveGamma) * kBT * Math.log(prob / (opesData.epsilon || 1e-18) + 1);
          }
        }
        gridPoints.push({ s: parseFloat(s.toFixed(3)), fes: parseFloat(fesVal.toFixed(2)) });
      }
    } else {
      let maxLogW = -Infinity;
      for (let k = 0; k < activeKernels.length; k++) {
        const lw = activeKernels[k].logweight !== undefined
          ? activeKernels[k].logweight
          : Math.log(Math.max(activeKernels[k].height, 1e-300));
        if (lw > maxLogW) maxLogW = lw;
      }
      let sumExpW = 0;
      for (let k = 0; k < activeKernels.length; k++) {
        const lw = activeKernels[k].logweight !== undefined
          ? activeKernels[k].logweight
          : Math.log(Math.max(activeKernels[k].height, 1e-300));
        sumExpW += Math.exp(lw - maxLogW);
      }
      const logWtot = maxLogW + Math.log(sumExpW);

      const logProbs = new Float64Array(bins);
      let maxLogProb = -Infinity;
      let minLogProb = Infinity;

      for (let i = 0; i < bins; i++) {
        const s = startZ + i * stepZ;
        let maxLogVal = -Infinity;
        const logVals = [];
        for (let k = 0; k < activeKernels.length; k++) {
          const kern = activeKernels[k];
          const diff = s - kern.z;
          const arg  = (diff * diff) / (2 * kern.sigma * kern.sigma);
          if (arg < 30.0) {
            const lw = kern.logweight !== undefined ? kern.logweight : Math.log(Math.max(kern.height, 1e-300));
            const val = lw - Math.log(Math.sqrt(2 * Math.PI) * kern.sigma) - arg;
            logVals.push(val);
            if (val > maxLogVal) maxLogVal = val;
          }
        }
        if (logVals.length > 0 && maxLogVal > -Infinity) {
          let sumExp = 0;
          for (let j = 0; j < logVals.length; j++) sumExp += Math.exp(logVals[j] - maxLogVal);
          const logP = (maxLogVal + Math.log(sumExp)) - logWtot;
          logProbs[i] = logP;
          if (logP > maxLogProb) maxLogProb = logP;
          if (logP < minLogProb) minLogProb = logP;
        } else {
          logProbs[i] = -Infinity;
        }
      }

      for (let i = 0; i < bins; i++) {
        const s    = startZ + i * stepZ;
        const logP = logProbs[i];
        let fesVal = 0;
        if (logP > -Infinity && maxLogProb > -Infinity) {
          if (energyRefMode === "plateauZero") {
            fesVal = -kBT * (logP - minLogProb);
          } else if (energyRefMode === "minZero") {
            fesVal = kBT * (maxLogProb - logP);
          } else {
            fesVal = (1 - 1 / effectiveGamma) * kBT * Math.log(Math.exp(logP) / (opesData.epsilon || 1e-18) + 1);
          }
        }
        gridPoints.push({ s: parseFloat(s.toFixed(3)), fes: parseFloat(fesVal.toFixed(2)) });
      }
    }

    return { gridPoints, sampleTime, activeCount: activeKernels.length, startZ, endZ };
  }, [opesData, numBins, gridMinUser, gridMaxUser, energyRefMode, energyUnits, inputCustomBias]);

  // ─── Rendered frame state (updated imperatively to decouple heavy calc from render) ───
  const [currentFrameData, setCurrentFrameData] = useState(null);

  // Recompute whenever static params change (not during animation)
  useEffect(() => {
    const frame = computeFrameData(timeStepProgress);
    setCurrentFrameData(frame);
  }, [computeFrameData]); // eslint-disable-line react-hooks/exhaustive-deps

  // Recompute when slider is moved manually (not during rAF animation)
  const lastProgressRef = useRef(timeStepProgress);
  useEffect(() => {
    if (!isPlayingTime) {
      lastProgressRef.current = timeStepProgress;
      const frame = computeFrameData(timeStepProgress);
      setCurrentFrameData(frame);
    }
  }, [timeStepProgress, isPlayingTime, computeFrameData]);

  // ─── rAF-based animation: advances progress + computes FES in one shot ───────
  const rafRef = useRef(null);
  const progressRef = useRef(timeStepProgress);

  useEffect(() => {
    progressRef.current = timeStepProgress;
  }, [timeStepProgress]);

  useEffect(() => {
    if (!isPlayingTime) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      return;
    }

    // How many percentage points to advance per frame (target ~30fps feel).
    // For large files with many kernels the computation already throttles naturally.
    const stepPerFrame = Math.max(1, Math.ceil(opesData?.kernels?.length / 2000) );

    const tick = () => {
      const next = progressRef.current + stepPerFrame;
      if (next >= 100) {
        progressRef.current = 100;
        setTimeStepProgress(100);
        const frame = computeFrameData(100);
        setCurrentFrameData(frame);
        setIsPlayingTime(false);
        return;
      }
      progressRef.current = next;
      setTimeStepProgress(next);
      const frame = computeFrameData(next);
      setCurrentFrameData(frame);
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [isPlayingTime, computeFrameData, opesData]);

  const handleApplyGridParams = (e) => {
    if (e) e.preventDefault();
    setNumBins(parseInt(inputNumBins) || 300);
    setGridMinUser(inputGridMin);
    setGridMaxUser(inputGridMax);
  };

  const handleResetGridBounds = () => {
    setInputGridMin("");
    setInputGridMax("");
    setGridMinUser("");
    setGridMaxUser("");
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`flex flex-col w-full h-full space-y-4 relative ${
        isDraggingFile ? "ring-4 ring-amber-500/80 bg-amber-950/20" : ""
      }`}
    >
      {/* Full Window Drag & Drop Overlay */}
      {isDraggingFile && (
        <div className="fixed inset-0 z-50 bg-amber-950/90 backdrop-blur-md border-4 border-dashed border-amber-500 flex flex-col items-center justify-center p-8 text-center animate-fadeIn pointer-events-none">
          <Upload size={64} className="text-amber-400 animate-bounce mb-4" />
          <h2 className="text-2xl font-black text-white">Drop your OPES_STATE file here</h2>
          <p className="text-sm text-amber-300">Requires a valid PLUMED OPES_STATE file</p>
        </div>
      )}

      {/* Mandatory OPES_STATE Pop-Up Alert Modal */}
      {errorMsg && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border-2 border-red-500/80 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-2xl">
                <AlertTriangle size={28} />
              </div>
              <div>
                <h3 className="font-extrabold text-base text-white">OPES_STATE File Mandatory</h3>
                <p className="text-[11px] text-red-400 font-mono">Invalid or unsupported OPES file format</p>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-slate-950 p-3.5 rounded-2xl border border-slate-800 font-mono">
              {errorMsg}
            </p>

            <div className="flex justify-end pt-1">
              <button
                onClick={() => setErrorMsg("")}
                className="py-2.5 px-6 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-bold rounded-xl text-xs shadow-lg transition-all"
              >
                Understand & Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Banner Header */}
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-xl flex justify-between items-center flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg shadow-amber-500/20 text-white">
            <Zap size={20} />
          </div>
          <div>
            <h1 className="font-extrabold text-sm text-white tracking-wide">
              PLUMED OPES Inspector & Visualizer
            </h1>
            <p className="text-xs text-amber-400 font-mono font-medium">
              On-the-fly Probability Enhanced Sampling (State Analysis)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="py-2 px-4 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md"
          >
            <Upload size={16} />
            <span>Upload OPES File</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".dat,.txt,.state,.kernels,*"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </header>

      {/* Main 2-Column Inspector Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Column 2: OPES Control Panel */}
        {opesData && (
          <div className="lg:col-span-3 space-y-4">
            <OpesControlPanel
              energyRefMode={energyRefMode}
              setEnergyRefMode={setEnergyRefMode}
              inputNumBins={inputNumBins}
              setInputNumBins={setInputNumBins}
              inputCustomBias={inputCustomBias}
              setInputCustomBias={setInputCustomBias}
              energyUnits={energyUnits}
              setEnergyUnits={setEnergyUnits}
              inputGridMin={inputGridMin}
              setInputGridMin={setInputGridMin}
              inputGridMax={inputGridMax}
              setInputGridMax={setInputGridMax}
              handleApplyGridParams={handleApplyGridParams}
              handleResetGridBounds={handleResetGridBounds}
              opesMetadata={opesData}
            />
          </div>
        )}

        {/* Column 3: Main Visualizer Content */}
        <div className={opesData ? "lg:col-span-9 space-y-4" : "lg:col-span-12 space-y-4"}>
          {/* EMPTY STATE DROPZONE */}
          {!opesData && !isLoading && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className="bg-slate-900/90 backdrop-blur-xl border-2 border-dashed border-slate-800 hover:border-amber-500/50 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-6 shadow-2xl transition-all"
            >
              <div className="p-5 bg-gradient-to-br from-amber-500/20 to-orange-600/20 border border-amber-500/30 rounded-2xl text-amber-400 shadow-xl shadow-amber-500/10">
                <Upload size={48} className="animate-pulse" />
              </div>
              <div className="max-w-md space-y-2">
                <h2 className="text-xl font-extrabold text-white">OPES_STATE File Visualizer (PLUMED)</h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Drag your <code className="text-amber-300 bg-slate-950 px-1.5 py-0.5 rounded font-mono">OPES_STATE</code> file directly onto this window or click the button to select it.
                </p>
              </div>

              <button
                onClick={() => fileInputRef.current?.click()}
                className="py-3 px-6 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-2xl text-xs font-bold flex items-center gap-2.5 transition-all shadow-xl shadow-amber-600/25 hover:scale-105"
              >
                <Upload size={18} />
                <span>Select OPES_STATE File</span>
              </button>
            </div>
          )}

          {/* Key Metrics Cards Dashboard */}
          {opesData && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Layers size={13} className="text-amber-400" /> Total Kernels
                </span>
                <span className="text-xl font-extrabold text-white mt-1 font-mono">
                  {opesData.counter}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">{fileType} File</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Clock size={13} className="text-cyan-400" /> Total Time
                </span>
                <span className="text-xl font-extrabold text-cyan-300 mt-1 font-mono">
                  {opesData.totalTime} <span className="text-xs font-sans text-slate-400">ps</span>
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Simulation time</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Award size={13} className="text-purple-400" /> Bias Factor (γ)
                </span>
                <span className="text-xl font-extrabold text-purple-300 mt-1 font-mono">
                  {opesData.biasFactor.toFixed(1)}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Target distribution</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp size={13} className="text-emerald-400" /> Partition Z (zed)
                </span>
                <span className="text-lg font-bold text-emerald-300 mt-1 font-mono truncate">
                  {opesData.zed > 0 ? opesData.zed.toFixed(4) : "Dynamic"}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Normalizer</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Activity size={13} className="text-amber-400" /> CV Range [z]
                </span>
                <span className="text-xs font-bold text-amber-300 mt-1 font-mono truncate">
                  [{opesData.minZ.toFixed(2)}, {opesData.maxZ.toFixed(2)}]
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Observed domain</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Zap size={13} className="text-indigo-400" /> Cutoff Threshold
                </span>
                <span className="text-lg font-bold text-indigo-300 mt-1 font-mono">
                  {opesData.kernelCutoff.toFixed(2)}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Kernel radius</span>
              </div>
            </div>
          )}

          {/* Navigation Tabs Header */}
          {opesData && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-2 shadow-xl flex flex-wrap justify-between items-center gap-2">
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs flex-wrap gap-1">
                <button
                  onClick={() => setActiveTab("fes")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                    activeTab === "fes"
                      ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md shadow-amber-500/20"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <TrendingUp size={15} /> Free Energy Surface F(z)
                </button>

                <button
                  onClick={() => setActiveTab("height")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                    activeTab === "height"
                      ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md shadow-amber-500/20"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Zap size={15} /> State Heights & Amplitudes
                </button>

                <button
                  onClick={() => setActiveTab("cv")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                    activeTab === "cv"
                      ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md shadow-amber-500/20"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Activity size={15} /> CV Trajectory z(t)
                </button>

                <button
                  onClick={() => setActiveTab("theory")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                    activeTab === "theory"
                      ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-md shadow-amber-500/20"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <BookOpen size={15} /> OPES Principles & Equations
                </button>
              </div>

              {/* File Name Tag */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
                <FileText size={14} className="text-amber-400" />
                <span>{fileName || "No file loaded"}</span>
              </div>
            </div>
          )}

          {/* TAB 1: Free Energy Surface F(z) */}
          {opesData && activeTab === "fes" && currentFrameData && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-2xl space-y-4 w-full">
              <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-2">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <TrendingUp size={20} className="text-amber-400" />
                    Reconstructed OPES Free Energy Profile F(z)
                  </h2>
                  <p className="text-slate-400 text-xs mt-0.5">
                    On-the-fly probability density estimation converted to Free Energy
                  </p>
                </div>
              </div>

              {/* Play / Pause Time Slider Bar */}
              <div className="bg-slate-950/80 border border-slate-800/80 p-3 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        if (!isPlayingTime && timeStepProgress >= 100) {
                          setTimeStepProgress(0);
                        }
                        setIsPlayingTime(!isPlayingTime);
                      }}
                      className={`py-1 px-3 rounded-lg font-bold text-xs shadow-md flex items-center gap-1.5 transition-all ${
                        isPlayingTime
                          ? "bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20"
                          : "bg-emerald-500 text-slate-950 hover:bg-emerald-400 shadow-emerald-500/20"
                      }`}
                    >
                      {isPlayingTime ? <><Pause size={13} /> PAUSE</> : <><Play size={13} /> PLAY</>}
                    </button>

                    <button
                      onClick={() => setTimeStepProgress(0)}
                      className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 rounded-lg border border-slate-800"
                      title="Reset to 0%"
                    >
                      <RotateCcw size={13} />
                    </button>
                  </div>

                  <span className="font-mono text-amber-400 font-bold text-xs">
                    State Entry {currentFrameData.activeCount} of {opesData.kernels.length} ({timeStepProgress}%) • t = {currentFrameData.sampleTime.toFixed(1)} ps
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={timeStepProgress}
                    onChange={(e) => setTimeStepProgress(parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                  />
                </div>
              </div>

              {/* FES Chart */}
              <div className="h-[340px] w-full pt-1 select-none">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={currentFrameData.gridPoints}
                    margin={{ top: 15, right: 25, left: 10, bottom: 20 }}
                  >
                    <defs>
                      <linearGradient id="opesFesGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.65} />
                        <stop offset="95%" stopColor="#d97706" stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="s"
                      type="number"
                      domain={['dataMin', 'dataMax']}
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 12 }}
                      label={{
                        value: "Collective Variable (z)",
                        position: "insideBottom",
                        offset: -12,
                        fill: "#cbd5e1",
                        fontSize: 13
                      }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 12 }}
                      label={{
                        value: `Free Energy F(z) [${energyUnits}]`,
                        angle: -90,
                        position: "insideLeft",
                        offset: 10,
                        fill: "#cbd5e1",
                        fontSize: 13
                      }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950/95 border border-slate-800 p-3 rounded-xl shadow-2xl text-xs space-y-1">
                              <div className="font-mono text-amber-400 font-bold border-b border-slate-800 pb-1">
                                z: {d.s}
                              </div>
                              <div className="text-amber-300 font-semibold">
                                F(z): {d.fes} {energyUnits}
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="fes"
                      stroke="#f59e0b"
                      strokeWidth={2.8}
                      fill="url(#opesFesGradient)"
                      isAnimationActive={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 2: State Heights & Amplitudes */}
          {opesData && activeTab === "height" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4 w-full">
              <div className="border-b border-slate-800 pb-3">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Zap size={18} className="text-amber-400" />
                  OPES State Heights & Amplitudes
                </h2>
                <p className="text-slate-400 text-xs">
                  Evolution of deposited kernel weights during sampling
                </p>
              </div>

              <div className="h-[400px] w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={opesData.kernels} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="idx"
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{ value: "Kernel Index (#)", position: "insideBottom", offset: -12, fill: "#cbd5e1", fontSize: 12 }}
                    />
                    <YAxis stroke="#64748b" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-xl shadow-xl text-xs space-y-1">
                              <div className="text-amber-400 font-mono font-bold">Kernel #{d.idx} (t = {d.time} ps)</div>
                              <div className="text-white font-semibold">Height: {d.height}</div>
                              {d.logweight !== undefined && (
                                <div className="text-slate-400 text-[10px]">logweight: {d.logweight}</div>
                              )}
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line type="monotone" dataKey="height" name="Kernel Height" stroke="#f59e0b" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 3: CV Trajectory z(t) */}
          {opesData && activeTab === "cv" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4 w-full">
              <div className="border-b border-slate-800 pb-3">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Activity size={18} className="text-cyan-400" />
                  Collective Variable Trajectory z(t) over Time
                </h2>
                <p className="text-slate-400 text-xs">
                  System diffusion along the collective variable coordinate
                </p>
              </div>

              <div className="h-[400px] w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={opesData.kernels} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="idx"
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{ value: "Kernel Index / Step (#)", position: "insideBottom", offset: -12, fill: "#cbd5e1", fontSize: 12 }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{ value: "Collective Variable (z)", angle: -90, position: "insideLeft", offset: 10, fill: "#cbd5e1", fontSize: 12 }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-xl shadow-xl text-xs space-y-1">
                              <div className="text-cyan-400 font-mono font-bold">Kernel #{d.idx} (t = {d.time} ps)</div>
                              <div className="text-white font-semibold">CV z: {d.z?.toFixed(4)}</div>
                              <div className="text-slate-400 text-[10px]">sigma: {d.sigma?.toFixed(4)}</div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line type="monotone" dataKey="z" name="CV position z" stroke="#06b6d4" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 4: OPES Principles & Equations Guide */}
          {opesData && activeTab === "theory" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 text-slate-200">
              <div className="border-b border-slate-800 pb-3">
                <h2 className="text-lg font-extrabold text-white flex items-center gap-2">
                  <BookOpen size={20} className="text-amber-400" />
                  On-the-fly Probability Enhanced Sampling (OPES) Principles
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Invernizzi & Parrinello, J. Phys. Chem. Lett. 2020, 11, 2731–2737
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed">
                <div className="bg-slate-950/80 border border-slate-800/80 p-4 rounded-xl space-y-3">
                  <h3 className="font-bold text-amber-400 text-sm flex items-center gap-2">
                    <Zap size={16} /> 1. Target Probability & Bias Potential
                  </h3>
                  <p>
                    Unlike standard Metadynamics which adds hills statically, OPES directly targets a pre-defined well-tempered distribution <MathInline tex="P_{target}(s) \propto [P(s)]^{1/\gamma}" />.
                  </p>
                  <p>The OPES bias potential <MathInline tex="V(s)" /> is defined as:</p>
                  <MathBlock tex="V(s) = \left(1 - \frac{1}{\gamma}\right) \frac{1}{\beta} \log \left( \frac{P(s)}{\epsilon} + 1 \right)" />
                  <p className="text-slate-400 text-[11px]">
                    where <MathInline tex="\gamma" /> is the bias factor and <MathInline tex="\epsilon" /> prevents numerical divergence in unexplored regions.
                  </p>
                </div>

                <div className="bg-slate-950/80 border border-slate-800/80 p-4 rounded-xl space-y-3">
                  <h3 className="font-bold text-cyan-400 text-sm flex items-center gap-2">
                    <Layers size={16} /> 2. Kernel Estimation & Partition Function Z
                  </h3>
                  <p>
                    The probability distribution <MathInline tex="P(s)" /> is estimated on-the-fly by summing adaptive Gaussian kernels:
                  </p>
                  <MathBlock tex="P(s) = \frac{1}{Z} \sum_{k} h_k \exp\left( - \frac{(s - z_k)^2}{2 \sigma_k^2} \right)" />
                  <p>
                    The partition function normalizer <MathInline tex="Z" /> (`zed` in PLUMED state) is tracked as kernels accumulate:
                  </p>
                  <MathBlock tex="Z = \frac{1}{N} \sum_{k=1}^N w_k" />
                </div>
              </div>

              <div className="bg-slate-950/80 border border-slate-800/80 p-4 rounded-xl text-xs space-y-2">
                <h3 className="font-bold text-purple-400 text-sm flex items-center gap-2">
                  <BarChart2 size={16} /> 3. Difference between OPES_KERNELS and OPES_STATE
                </h3>
                <ul className="list-disc list-inside space-y-1.5 text-slate-300">
                  <li>
                    <strong className="text-amber-300 font-mono">OPES_KERNELS</strong>: Stores every individual kernel deposited during the simulation with its timestamp `time`, position `z`, bandwidth `sigma_z`, amplitude `height`, and `logweight`. Allows full time-series animation of convergence.
                  </li>
                  <li>
                    <strong className="text-cyan-300 font-mono">OPES_STATE</strong>: Stores the compressed, consolidated distribution state at a given checkpoint, including global normalizers `zed` ($Z$) and `sum_weights`. Ideal for fast restart and static FES calculation.
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

EOF

echo "=== Writing src/HillsVisualizer.jsx ==="
cat << 'EOF' > src/HillsVisualizer.jsx
import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Upload,
  FileText,
  TrendingUp,
  Activity,
  Layers,
  Download,
  BarChart2,
  Clock,
  Zap,
  Sliders,
  RotateCcw,
  Play,
  Pause,
  Loader2,
  Award,
  AlertTriangle,
  RefreshCw,
  Image as ImageIcon,
  ZoomIn,
  X,
  ShieldCheck
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
  ReferenceArea,
  ReferenceLine
} from "recharts";

// --- React Error Boundary ---
class HillsErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("HillsVisualizer Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-950/90 border border-red-800 text-slate-100 p-6 rounded-2xl shadow-2xl space-y-4 max-w-3xl mx-auto my-8">
          <div className="flex items-center gap-3 text-red-400 font-bold text-lg">
            <AlertTriangle size={24} />
            <span>Error Processing HILLS File</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            An error occurred during data processing or rendering.
          </p>
          <pre className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-xs text-red-300 overflow-x-auto">
            {this.state.error?.toString() || "Unknown execution error"}
          </pre>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                if (this.props.onReset) this.props.onReset();
              }}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-md"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// --- Safe Array Min/Max Helper (No Call Stack Overflow) ---
function getMinMax(arr, defaultVal = 0) {
  if (!arr || arr.length === 0) return { min: defaultVal, max: defaultVal };
  let min = Infinity;
  let max = -Infinity;
  for (let i = 0; i < arr.length; i++) {
    const v = arr[i];
    if (typeof v === "number" && !isNaN(v)) {
      if (v < min) min = v;
      if (v > max) max = v;
    }
  }
  if (min === Infinity) min = defaultVal;
  if (max === -Infinity) max = defaultVal;
  return { min, max };
}

// --- Downsampling helper for charts ---
function downsampleArray(arr, maxPoints = 800) {
  if (!arr || arr.length <= maxPoints) return arr;
  const step = arr.length / maxPoints;
  const result = [];
  for (let i = 0; i < maxPoints; i++) {
    const idx = Math.floor(i * step);
    result.push(arr[idx]);
  }
  if (result[result.length - 1] !== arr[arr.length - 1]) {
    result.push(arr[arr.length - 1]);
  }
  return result;
}

// --- Color Generator for 2D FES Heatmap ---
function getHeatmapColor(val, minVal, maxVal, palette = "Viridis") {
  const range = maxVal - minVal;
  const norm = range > 0.0001 ? Math.max(0, Math.min(1, (val - minVal) / range)) : 0;

  if (palette === "Inferno") {
    const inv = 1 - norm;
    const r = Math.floor(255 * Math.pow(inv, 0.5));
    const g = Math.floor(255 * Math.pow(inv, 1.5));
    const b = Math.floor(255 * Math.pow(inv, 3.0));
    return `rgb(${r},${g},${b})`;
  } else if (palette === "Spectral") {
    const h = (1 - norm) * 240;
    const l = 15 + norm * 35;
    return `hsl(${h}, 85%, ${l}%)`;
  } else if (palette === "CoolWarm") {
    const r = Math.floor(20 + norm * 200);
    const g = Math.floor(180 * (1 - norm));
    const b = Math.floor(240 * (1 - norm * 0.8));
    return `rgb(${r},${g},${b})`;
  } else {
    // Viridis (Scientific Default)
    const inv = 1 - norm;
    const r = Math.floor(255 * Math.sin(inv * Math.PI * 0.5));
    const g = Math.floor(255 * Math.pow(inv, 0.8));
    const b = Math.floor(80 + 175 * Math.sin(inv * Math.PI));
    return `rgb(${r},${g},${b})`;
  }
}

// --- 1D PMF Plot Exporter matching Matplotlib plot_single_fes_dat layout (No Title, No Badge) ---
function export1DPlot({
  gridPoints,
  cvName,
  energyUnits,
  energyRefMode = "plateauZero",
  format = "png",
  transparent = false
}) {
  if (!gridPoints || gridPoints.length === 0) return;

  const width = 1200;
  const height = 760;
  const padLeft = 110;
  const padRight = 60;
  const padTop = 105;
  const padBottom = 85;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const sVals = gridPoints.map((p) => p.s);
  const fesVals = gridPoints.map((p) => p.fes);

  const { min: minS, max: maxS } = getMinMax(sVals, 0);
  const rangeS = maxS - minS || 1;

  // 1. Minimum Position & Minimum Energy strictly inside current ROI grid points
  let minIdx = 0;
  let minFES = fesVals[0];
  for (let i = 1; i < fesVals.length; i++) {
    if (fesVals[i] < minFES) {
      minFES = fesVals[i];
      minIdx = i;
    }
  }
  const minS_val = sVals[minIdx];

  // 2. Plateau detection via sliding-window variance minimisation
  // Searches for the flattest contiguous segment (≥15% of total points, min 3 pts).
  // Only considers segments that are OUTSIDE the minimum well neighbourhood (avoids
  // mistaking a very shallow well bottom for a plateau).
  const n = gridPoints.length;
  const winSize = Math.max(3, Math.round(n * 0.15)); // 15% window, at least 3 pts

  let bestVar = Infinity;
  let bestWinStart = Math.max(0, n - winSize); // fallback: rightmost window

  for (let i = 0; i <= n - winSize; i++) {
    // Compute mean of FES in this window
    let sum = 0;
    for (let j = i; j < i + winSize; j++) sum += fesVals[j];
    const mean = sum / winSize;

    // Compute variance
    let varAcc = 0;
    for (let j = i; j < i + winSize; j++) {
      const d = fesVals[j] - mean;
      varAcc += d * d;
    }
    const variance = varAcc / winSize;

    // Prefer the flattest window that does NOT straddle the global minimum
    // (to avoid selecting the bottom of a deep but narrow well)
    const windowContainsMin = minIdx >= i && minIdx < i + winSize;
    if (!windowContainsMin && variance < bestVar) {
      bestVar = variance;
      bestWinStart = i;
    }
  }

  // If every window contained the minimum (e.g. very simple monotonic curve),
  // fall back to the rightmost window regardless.
  if (bestVar === Infinity) {
    bestWinStart = Math.max(0, n - winSize);
  }

  const plateauPts = gridPoints.slice(bestWinStart, bestWinStart + winSize);
  let plateauSumY = 0;
  let plateauSumX = 0;
  plateauPts.forEach((p) => {
    plateauSumY += p.fes;
    plateauSumX += p.s;
  });
  const platYVal = plateauPts.length > 0 ? plateauSumY / plateauPts.length : fesVals[fesVals.length - 1];
  const platXVal = plateauPts.length > 0 ? plateauSumX / plateauPts.length : maxS;

  const { min: minY, max: maxY } = getMinMax(fesVals, 0);
  const rangeY = maxY - minY || 1;

  // PMF Curve Points
  const points = gridPoints.map((p) => {
    const px = padLeft + ((p.s - minS) / rangeS) * plotW;
    const py = padTop + plotH - ((p.fes - minY) / rangeY) * plotH;
    return `${px.toFixed(2)},${py.toFixed(2)}`;
  });
  const pointsString = points.join(" ");

  // Shaded Region under y=0 (where fes <= 0)
  const zeroPy = padTop + plotH - ((0 - minY) / rangeY) * plotH;
  let shadedPath = "";
  const shadedPoints = [];
  gridPoints.forEach((p) => {
    if (p.fes <= 0) {
      const px = padLeft + ((p.s - minS) / rangeS) * plotW;
      const py = padTop + plotH - ((p.fes - minY) / rangeY) * plotH;
      shadedPoints.push({ px, py });
    }
  });

  if (shadedPoints.length > 0) {
    const first = shadedPoints[0];
    const last = shadedPoints[shadedPoints.length - 1];
    let pathD = `M ${first.px.toFixed(2)} ${zeroPy.toFixed(2)} `;
    shadedPoints.forEach((pt) => {
      pathD += `L ${pt.px.toFixed(2)} ${pt.py.toFixed(2)} `;
    });
    pathD += `L ${last.px.toFixed(2)} ${zeroPy.toFixed(2)} Z`;
    shadedPath = pathD;
  }

  // Key Line Positions
  const minPx = padLeft + ((minS_val - minS) / rangeS) * plotW;
  const minPy = padTop + plotH - ((minFES - minY) / rangeY) * plotH;
  const bulkPx = padLeft + ((platXVal - minS) / rangeS) * plotW;
  const platPy = padTop + plotH - ((platYVal - minY) / rangeY) * plotH;

  // Plateau window band edges (for shaded rectangle in export)
  const platSMin = plateauPts[0].s;
  const platSMax = plateauPts[plateauPts.length - 1].s;
  const platBandX1 = padLeft + ((platSMin - minS) / rangeS) * plotW;
  const platBandX2 = padLeft + ((platSMax - minS) / rangeS) * plotW;
  const platBandW = Math.max(1, platBandX2 - platBandX1);

  const bgColorAttr = transparent ? "none" : "#ffffff";
  const textColor = "#1e293b";
  const axisColor = "#334155";
  const gridColor = "#e2e8f0";

  // Exact Colors matching Matplotlib PMF_subplots / plot_single_fes_dat
  const COLOR_CURVE = "#08306A";     // Dark Navy Blue
  const COLOR_MIN_X = "#860203";     // Dark Red
  const COLOR_PLATEAU_X = "#2B8092"; // Teal
  const COLOR_PLATEAU_Y = "#959800"; // Olive

  // X Ticks (Integer values)
  let xTicksHTML = "";
  const startInt = Math.ceil(minS);
  const endInt = Math.floor(maxS);
  if (endInt >= startInt && (endInt - startInt) >= 1) {
    const intRange = endInt - startInt;
    const step = intRange <= 12 ? 1 : Math.ceil(intRange / 10);
    for (let val = startInt; val <= endInt; val += step) {
      const frac = (val - minS) / rangeS;
      const px = padLeft + frac * plotW;
      xTicksHTML += `
        <line x1="${px}" y1="${padTop}" x2="${px}" y2="${padTop + plotH}" stroke="${gridColor}" stroke-dasharray="3,3" />
        <line x1="${px}" y1="${padTop + plotH}" x2="${px}" y2="${padTop + plotH + 6}" stroke="${axisColor}" stroke-width="1.5" />
        <text x="${px}" y="${padTop + plotH + 26}" fill="${textColor}" font-family="Inter, sans-serif" font-size="16" font-weight="bold" text-anchor="middle">${val}</text>
      `;
    }
  }

  // Y Ticks
  let yTicksHTML = "";
  const numYTicks = 5;
  for (let t = 0; t <= numYTicks; t++) {
    const frac = t / numYTicks;
    const yVal = Math.round(minY + frac * rangeY);
    const py = padTop + plotH - frac * plotH;
    yTicksHTML += `
      <line x1="${padLeft}" y1="${py}" x2="${padLeft + plotW}" y2="${py}" stroke="${gridColor}" stroke-dasharray="3,3" />
      <line x1="${padLeft - 6}" y1="${py}" x2="${padLeft}" y2="${py}" stroke="${axisColor}" stroke-width="1.5" />
      <text x="${padLeft - 12}" y="${py + 5}" fill="${textColor}" font-family="Inter, sans-serif" font-size="15" font-weight="bold" text-anchor="end">${yVal}</text>
    `;
  }

  // Build SVG XML matching Matplotlib plot (No Title, No Badge)
  const svgString = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}">
    <style>
      .bg { fill: ${bgColorAttr}; }
      .axis-label { fill: ${textColor}; font-family: Inter, sans-serif; font-weight: bold; font-size: 18px; }
      .annot-text { font-family: Inter, sans-serif; font-weight: bold; font-size: 16px; }
      .legend-text { fill: #1e293b; font-family: Inter, sans-serif; font-size: 14px; font-weight: 600; }
    </style>
    ${transparent ? "" : `<rect width="${width}" height="${height}" class="bg" />`}

    <!-- Grid Lines -->
    ${xTicksHTML}
    ${yTicksHTML}

    <!-- Auto-detected Plateau Window Shaded Band (Teal) -->
    <rect x="${platBandX1.toFixed(2)}" y="${padTop}" width="${platBandW.toFixed(2)}" height="${plotH}" fill="${COLOR_PLATEAU_X}" fill-opacity="0.12" />
    <line x1="${platBandX1.toFixed(2)}" y1="${padTop}" x2="${platBandX1.toFixed(2)}" y2="${padTop + plotH}" stroke="${COLOR_PLATEAU_X}" stroke-width="1.2" stroke-dasharray="4,3" opacity="0.7" />
    <line x1="${platBandX2.toFixed(2)}" y1="${padTop}" x2="${platBandX2.toFixed(2)}" y2="${padTop + plotH}" stroke="${COLOR_PLATEAU_X}" stroke-width="1.2" stroke-dasharray="4,3" opacity="0.7" />

    <!-- Shaded DeltaG Region (Olive Green Fill) -->
    ${shadedPath ? `<path d="${shadedPath}" fill="${COLOR_PLATEAU_Y}" fill-opacity="0.20" />` : ""}

    <!-- Plateau Reference Horizontal Line -->
    <line x1="${padLeft}" y1="${platPy.toFixed(2)}" x2="${padLeft + plotW}" y2="${platPy.toFixed(2)}" stroke="black" stroke-width="1.5" stroke-dasharray="5,5" opacity="0.8" />

    <!-- Minimum Energy Dotted Horizontal Line -->
    <line x1="${padLeft}" y1="${minPy}" x2="${padLeft + plotW}" y2="${minPy}" stroke="${COLOR_PLATEAU_Y}" stroke-width="1.8" stroke-dasharray="2,3" opacity="0.9" />

    <!-- Minimum Position Vertical Line (Dark Red) -->
    <line x1="${minPx}" y1="${padTop}" x2="${minPx}" y2="${padTop + plotH}" stroke="${COLOR_MIN_X}" stroke-width="1.8" stroke-dasharray="6,4" />

    <!-- Plateau Centroid Vertical Line (Teal) -->
    <line x1="${bulkPx}" y1="${padTop}" x2="${bulkPx}" y2="${padTop + plotH}" stroke="${COLOR_PLATEAU_X}" stroke-width="1.8" stroke-dasharray="6,4" />

    <!-- PMF Curve Line (Dark Navy Blue) -->
    <polyline points="${pointsString}" fill="none" stroke="${COLOR_CURVE}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" />

    <!-- Outer Frame Box -->
    <rect x="${padLeft}" y="${padTop}" width="${plotW}" height="${plotH}" fill="none" stroke="${axisColor}" stroke-width="2" />

    <!-- Text Annotations directly above lines matching Matplotlib -->
    <!-- Red Minimum Position Text -->
    <text x="${minPx}" y="${padTop + 24}" fill="${COLOR_MIN_X}" class="annot-text" text-anchor="middle">${minS_val.toFixed(2)}</text>

    <!-- Teal Plateau Centroid Position Text -->
    <text x="${bulkPx}" y="${padTop + 48}" fill="${COLOR_PLATEAU_X}" class="annot-text" text-anchor="middle">${platXVal.toFixed(2)}</text>

    <!-- Olive Plateau Energy Text floating above dotted line -->
    <text x="${padLeft + 35}" y="${minPy - 10}" fill="${COLOR_PLATEAU_Y}" class="annot-text" text-anchor="start">${Math.abs(minFES).toFixed(2)}</text>

    <!-- Axis Titles -->
    <text x="${padLeft + plotW / 2}" y="${height - 20}" class="axis-label" text-anchor="middle">${cvName || "D.z"} (nm)</text>
    <text x="32" y="${padTop + plotH / 2}" class="axis-label" text-anchor="middle" transform="rotate(-90 32 ${padTop + plotH / 2})">Free Energy (${energyUnits})</text>

    <!-- Top Multicolumn Legend Box -->
    <g transform="translate(${padLeft + plotW / 2 - 395}, ${padTop - 55})">
      <rect x="0" y="0" width="750" height="34" rx="6" fill="white" stroke="#cbd5e1" stroke-width="1.2" />

      <!-- Item 1: PMF -->
      <line x1="18" y1="17" x2="45" y2="17" stroke="${COLOR_CURVE}" stroke-width="3" />
      <text x="52" y="21" class="legend-text">PMF</text>

      <!-- Item 2: Minimum (nm) -->
      <line x1="110" y1="17" x2="138" y2="17" stroke="${COLOR_MIN_X}" stroke-width="2" stroke-dasharray="5,3" />
      <text x="145" y="21" class="legend-text">Minimum (nm)</text>

      <!-- Item 3: Auto-plateau region -->
      <rect x="275" y="9" width="26" height="16" fill="${COLOR_PLATEAU_X}" fill-opacity="0.25" stroke="${COLOR_PLATEAU_X}" stroke-width="1.5" />
      <text x="308" y="21" class="legend-text">Plateau region (auto)</text>

      <!-- Item 4: Plateau energy -->
      <line x1="495" y1="17" x2="522" y2="17" stroke="${COLOR_PLATEAU_Y}" stroke-width="2" stroke-dasharray="2,2" />
      <text x="530" y="21" class="legend-text">Plateau energy (${energyUnits})</text>
    </g>
  </svg>`;

  if (format === "svg") {
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `PMF_${cvName}_profile.svg`;
    link.click();
    URL.revokeObjectURL(url);
  } else {
    const img = new Image();
    const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");

      if (!transparent) {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, width, height);
      } else {
        ctx.clearRect(0, 0, width, height);
      }

      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);

      canvas.toBlob((pngBlob) => {
        const pngUrl = URL.createObjectURL(pngBlob);
        const link = document.createElement("a");
        link.href = pngUrl;
        link.download = `PMF_${cvName}_profile.png`;
        link.click();
        URL.revokeObjectURL(pngUrl);
      }, "image/png");
    };
    img.src = url;
  }
}

// --- Inline Web Worker Creator supporting Ultra-Large Files (up to 1 GB+) & Fast Incremental Engine ---
function createHillsWorker() {
  const code = `
  self.onmessage = async function(e) {
    const file = e.data.file;
    const directText = e.data.text;
    const numBinsUser = e.data.numBins || 500;
    const isWtScaling = e.data.isWtScaling !== false;
    const customBiasFactor = e.data.customBiasFactor;
    const energyUnits = e.data.energyUnits || "kJ/mol";
    const gridMinUser = e.data.gridMinUser;
    const gridMaxUser = e.data.gridMaxUser;

    let fieldNames = [];
    let headerMeta = {};
    const rawRows = [];

    if (file) {
      const chunkSize = 15 * 1024 * 1024; // 15 MB chunks
      let offset = 0;
      let leftover = "";
      const fileSize = file.size;

      while (offset < fileSize) {
        const slice = file.slice(offset, offset + chunkSize);
        const textChunk = await slice.text();
        const fullText = leftover + textChunk;

        const lastNewline = fullText.lastIndexOf("\\n");
        let processable = fullText;
        if (lastNewline !== -1 && offset + chunkSize < fileSize) {
          processable = fullText.substring(0, lastNewline);
          leftover = fullText.substring(lastNewline + 1);
        } else {
          leftover = "";
        }

        const lines = processable.split("\\n");
        for (let i = 0; i < lines.length; i++) {
          const rawLine = lines[i].trim();
          if (!rawLine) continue;

          if (rawLine.startsWith("#!")) {
            const parts = rawLine.replace("#!", "").trim().split(/\\s+/);
            const key = parts[0]?.toUpperCase();
            if (key === "FIELDS") {
              fieldNames = parts.slice(1);
            } else if (key === "SET" && parts.length >= 3) {
              headerMeta[parts[1]] = parts[2];
            }
            continue;
          }

          if (rawLine.startsWith("#")) continue;

          const tokens = rawLine.split(/\\s+/).map((v) => parseFloat(v));
          if (tokens.length > 0 && !tokens.some((val) => isNaN(val))) {
            rawRows.push(tokens);
          }
        }

        offset += chunkSize;
        const pct = Math.min(45, Math.floor((offset / fileSize) * 45));
        self.postMessage({ progress: pct });
      }
    } else if (directText) {
      const lines = directText.split("\\n");
      for (let i = 0; i < lines.length; i++) {
        const rawLine = lines[i].trim();
        if (!rawLine) continue;
        if (rawLine.startsWith("#!")) {
          const parts = rawLine.replace("#!", "").trim().split(/\\s+/);
          const key = parts[0]?.toUpperCase();
          if (key === "FIELDS") fieldNames = parts.slice(1);
          else if (key === "SET" && parts.length >= 3) headerMeta[parts[1]] = parts[2];
          continue;
        }
        if (rawLine.startsWith("#")) continue;
        const tokens = rawLine.split(/\\s+/).map((v) => parseFloat(v));
        if (tokens.length > 0 && !tokens.some((val) => isNaN(val))) {
          rawRows.push(tokens);
        }
      }
    }

    if (rawRows.length === 0) {
      self.postMessage({ error: "No valid numeric data rows found in HILLS file." });
      return;
    }

    const dataRows = rawRows;

    if (fieldNames.length === 0) {
      const colCount = dataRows[0].length;
      if (colCount === 5) {
        fieldNames = ["time", "cv1", "sigma_cv1", "height", "biasf"];
      } else if (colCount === 4) {
        fieldNames = ["time", "cv1", "sigma_cv1", "height"];
      } else if (colCount >= 7) {
        fieldNames = ["time", "cv1", "cv2", "sigma_cv1", "sigma_cv2", "height", "biasf"];
      } else if (colCount === 6) {
        fieldNames = ["time", "cv1", "cv2", "sigma_cv1", "sigma_cv2", "height"];
      } else {
        fieldNames = Array.from({ length: colCount }, (_, idx) => "col_" + (idx + 1));
      }
    }

    const fieldLower = fieldNames.map((f) => f.toLowerCase());
    let timeIdx = fieldLower.indexOf("time");
    if (timeIdx === -1) timeIdx = 0;

    let heightIdx = fieldLower.findIndex((f) => f === "height" || f === "w" || f === "h");
    if (heightIdx === -1) heightIdx = fieldNames.length - 2 >= 0 ? fieldNames.length - 2 : 3;

    let biasfIdx = fieldLower.findIndex((f) => f === "biasf" || f === "biasfactor");
    if (biasfIdx === -1 && fieldNames.length >= 5 && fieldNames.length !== 6) {
      biasfIdx = fieldNames.length - 1;
    }

    const cvIndices = [];
    const sigmaIndices = [];

    fieldNames.forEach((name, idx) => {
      const n = name.toLowerCase();
      if (idx === timeIdx || idx === heightIdx || idx === biasfIdx) return;
      if (n === "clock" || n === "walker" || n === "replica" || n === "mult" || n.startsWith("clock") || n.startsWith("walker") || n.startsWith("mult") || n.startsWith("replica")) return;
      if (n.startsWith("sigma")) {
        sigmaIndices.push(idx);
      } else {
        cvIndices.push(idx);
      }
    });

    if (cvIndices.length === 0) {
      cvIndices.push(1);
      if (fieldNames.length > 2) sigmaIndices.push(2);
    }

    const is2D = cvIndices.length >= 2;

    self.postMessage({ progress: 46 });

    // Multi-walker detection BEFORE sorting
    let detectedWalkers = 1;

    // A. Initial timestamp duplicates
    let initSameCount = 1;
    const t0Val = rawRows[0] ? (rawRows[0][timeIdx] ?? 0) : 0;
    const t0Rounded = Math.round(t0Val * 100) / 100;
    while (
      initSameCount < rawRows.length &&
      Math.round((rawRows[initSameCount][timeIdx] ?? 0) * 100) / 100 === t0Rounded
    ) {
      initSameCount++;
    }

    // B. Timestamp drops (block multiwalker)
    const blockStartIndices = [0];
    for (let i = 1; i < rawRows.length; i++) {
      if ((rawRows[i][timeIdx] ?? 0) < (rawRows[i - 1][timeIdx] ?? 0)) {
        blockStartIndices.push(i);
      }
    }

    if (blockStartIndices.length > 1) {
      detectedWalkers = blockStartIndices.length;
    } else if (initSameCount >= 2) {
      detectedWalkers = initSameCount;
    } else {
      detectedWalkers = 1;
    }

    const isBlockStructure = blockStartIndices.length > 1 && blockStartIndices.length === detectedWalkers;
    const blockSize = isBlockStructure ? Math.ceil(rawRows.length / detectedWalkers) : 1;

    const parsedHills = rawRows.map((row, rowIdx) => {
      const timeVal = row[timeIdx] ?? rowIdx * 10;
      const heightVal = row[heightIdx] ?? 1.0;
      const biasfVal = biasfIdx !== -1 && biasfIdx < row.length ? row[biasfIdx] : null;

      const cvVals = cvIndices.map((ci) => row[ci] ?? 0.0);
      const sigmaVals = sigmaIndices.map((si) => row[si] ?? 0.1);

      let wId = 1;
      if (detectedWalkers > 1) {
        if (isBlockStructure) {
          wId = Math.min(detectedWalkers, Math.floor(rowIdx / blockSize) + 1);
        } else {
          wId = (rowIdx % detectedWalkers) + 1;
        }
      }

      return {
        step: rowIdx + 1,
        time: timeVal,
        cvs: cvVals,
        sigmas: sigmaVals,
        height: heightVal,
        biasf: biasfVal,
        walkerId: wId
      };
    });

    // Chronological sorting directly on raw number arrays (Fast & memory light)
    rawRows.sort((a, b) => (a[timeIdx] ?? 0) - (b[timeIdx] ?? 0));

    self.postMessage({ progress: 48 });

    const totalOriginalHills = parsedHills.length;
    const strideFactor = 1;

    self.postMessage({ progress: 50 });

    const cvNames = cvIndices.map((idx) => fieldNames[idx] || ("CV" + (cvIndices.indexOf(idx) + 1)));
    const startTime = parsedHills[0]?.time ?? 0;
    const endTime = parsedHills[parsedHills.length - 1]?.time ?? 0;

    let gamma = 1.0;
    if (customBiasFactor !== "" && !isNaN(parseFloat(customBiasFactor))) {
      gamma = parseFloat(customBiasFactor);
    } else if (parsedHills[0]?.biasf !== null && parsedHills[0]?.biasf > 1) {
      gamma = parsedHills[0].biasf;
    }
    const wtFactor = isWtScaling && gamma > 1 ? gamma / (gamma - 1) : 1.0;
    const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

    const numFrames = 101;
    const timelineGrids = new Array(numFrames);
    const chunkHillsCount = Math.ceil(parsedHills.length / 100);

    if (!is2D) {
      // --- 1D FES CALCULATION ENGINE ---
      const numBins = numBinsUser;
      let minCV = Infinity, maxCV = -Infinity;
      for (let h = 0; h < parsedHills.length; h++) {
        const v = parsedHills[h].cvs[0];
        if (v < minCV) minCV = v;
        if (v > maxCV) maxCV = v;
      }
      const avgSigma = parsedHills[0]?.sigmas[0] || 0.1;
      let gridMin = minCV - 4 * avgSigma;
      let gridMax = maxCV + 4 * avgSigma;

      if (gridMinUser !== "" && !isNaN(parseFloat(gridMinUser))) gridMin = parseFloat(gridMinUser);
      if (gridMaxUser !== "" && !isNaN(parseFloat(gridMaxUser))) gridMax = parseFloat(gridMaxUser);

      const stepSize = (gridMax - gridMin) / (numBins - 1);
      const accumulatedV = new Float64Array(numBins);

      // Frame 0 (0% time): Completely flat potential V=0 at t=0
      const frame0Grid = new Array(numBins);
      for (let i = 0; i < numBins; i++) {
        const s = gridMin + i * stepSize;
        frame0Grid[i] = {
          s: parseFloat(s.toFixed(4)),
          rawFes: 0,
          zeroFes: 0,
          vBiasRaw: 0
        };
      }
      timelineGrids[0] = {
        frameIndex: 0,
        pct: 0,
        sampleTime: startTime,
        activeHillsCount: 0,
        gridPoints: frame0Grid
      };

      for (let f = 1; f <= 100; f++) {
        const startH = (f - 1) * chunkHillsCount;
        const endH = Math.min(parsedHills.length, f * chunkHillsCount);
        const sampleTime = parsedHills[Math.min(parsedHills.length - 1, endH - 1)]?.time || 0;

        for (let h = startH; h < endH; h++) {
          const hill = parsedHills[h];
          const center = hill.cvs[0];
          const sigma = hill.sigmas[0] || avgSigma;
          const height = hill.height;
          if (height === 0 || sigma === 0) continue;
          const invTwoSigmaSq = 1.0 / (2 * sigma * sigma);

          const cutoff = 6.0 * sigma;
          const minI = Math.max(0, Math.floor((center - cutoff - gridMin) / stepSize));
          const maxI = Math.min(numBins - 1, Math.ceil((center + cutoff - gridMin) / stepSize));

          for (let i = minI; i <= maxI; i++) {
            const s = gridMin + i * stepSize;
            const diff = s - center;
            accumulatedV[i] += height * Math.exp(-(diff * diff) * invTwoSigmaSq);
          }
        }

        let minFES = Infinity;
        const rawF = new Float64Array(numBins);
        for (let i = 0; i < numBins; i++) {
          const val = -wtFactor * accumulatedV[i];
          rawF[i] = val;
          if (val < minFES) minFES = val;
        }

        const frameGrid = new Array(numBins);
        for (let i = 0; i < numBins; i++) {
          const s = gridMin + i * stepSize;
          frameGrid[i] = {
            s: parseFloat(s.toFixed(4)),
            rawFes: rawF[i],
            zeroFes: rawF[i] - minFES,
            vBiasRaw: accumulatedV[i]
          };
        }

        timelineGrids[f] = {
          frameIndex: f,
          pct: f,
          sampleTime,
          activeHillsCount: endH,
          gridPoints: frameGrid
        };

        if (f % 2 === 0 || f === 100) {
          self.postMessage({ progress: 50 + Math.floor((f / 100) * 50) });
        }
      }
    } else {
      // --- 2D FES CALCULATION ENGINE ---
      const numBinsX = 90;
      const numBinsY = 90;

      let minCV1 = Infinity, maxCV1 = -Infinity;
      let minCV2 = Infinity, maxCV2 = -Infinity;

      for (let h = 0; h < parsedHills.length; h++) {
        const v1 = parsedHills[h].cvs[0];
        const v2 = parsedHills[h].cvs[1];
        if (v1 < minCV1) minCV1 = v1;
        if (v1 > maxCV1) maxCV1 = v1;
        if (v2 < minCV2) minCV2 = v2;
        if (v2 > maxCV2) maxCV2 = v2;
      }

      const avgSig1 = parsedHills[0]?.sigmas[0] || 0.1;
      const avgSig2 = parsedHills[0]?.sigmas[1] || 0.1;

      let gridMin1 = minCV1 - 4 * avgSig1;
      let gridMax1 = maxCV1 + 4 * avgSig1;
      let gridMin2 = minCV2 - 4 * avgSig2;
      let gridMax2 = maxCV2 + 4 * avgSig2;

      if (gridMinUser !== "" && !isNaN(parseFloat(gridMinUser))) gridMin1 = parseFloat(gridMinUser);
      if (gridMaxUser !== "" && !isNaN(parseFloat(gridMaxUser))) gridMax1 = parseFloat(gridMaxUser);

      const stepX = (gridMax1 - gridMin1) / (numBinsX - 1);
      const stepY = (gridMax2 - gridMin2) / (numBinsY - 1);
      const accumulatedV2D = new Float64Array(numBinsX * numBinsY);

      // Frame 0 (0% time): Completely flat potential
      const grid2DFlat0 = new Float64Array(numBinsX * numBinsY * 2);
      const projCV1_0 = new Array(numBinsX);
      for (let i = 0; i < numBinsX; i++) {
        const s1 = gridMin1 + i * stepX;
        projCV1_0[i] = { s: parseFloat(s1.toFixed(4)), fesInt: 0, fesMin: 0, rawFesInt: 0, rawFesMin: 0 };
      }
      const projCV2_0 = new Array(numBinsY);
      for (let j = 0; j < numBinsY; j++) {
        const s2 = gridMin2 + j * stepY;
        projCV2_0[j] = { s: parseFloat(s2.toFixed(4)), fesInt: 0, fesMin: 0, rawFesInt: 0, rawFesMin: 0 };
      }

      timelineGrids[0] = {
        frameIndex: 0,
        pct: 0,
        sampleTime: startTime,
        activeHillsCount: 0,
        grid2DFlat: grid2DFlat0,
        projCV1: projCV1_0,
        projCV2: projCV2_0,
        numBinsX,
        numBinsY,
        gridMin1,
        gridMax1,
        gridMin2,
        gridMax2
      };

      for (let f = 1; f <= 100; f++) {
        const startH = (f - 1) * chunkHillsCount;
        const endH = Math.min(parsedHills.length, f * chunkHillsCount);
        const sampleTime = parsedHills[Math.min(parsedHills.length - 1, endH - 1)]?.time || 0;

        for (let h = startH; h < endH; h++) {
          const hill = parsedHills[h];
          const cx = hill.cvs[0];
          const cy = hill.cvs[1];
          const sigx = hill.sigmas[0] || avgSig1;
          const sigy = hill.sigmas[1] || avgSig2;
          const height = hill.height;
          if (height === 0 || sigx === 0 || sigy === 0) continue;

          const inv2SigXSq = 1.0 / (2 * sigx * sigx);
          const inv2SigYSq = 1.0 / (2 * sigy * sigy);

          // 6-sigma bounding box truncation (zero truncation error down to 10^-8 precision)
          const cutoffX = 6.0 * sigx;
          const cutoffY = 6.0 * sigy;

          const minI = Math.max(0, Math.floor((cx - cutoffX - gridMin1) / stepX));
          const maxI = Math.min(numBinsX - 1, Math.ceil((cx + cutoffX - gridMin1) / stepX));

          const minJ = Math.max(0, Math.floor((cy - cutoffY - gridMin2) / stepY));
          const maxJ = Math.min(numBinsY - 1, Math.ceil((cy + cutoffY - gridMin2) / stepY));

          for (let j = minJ; j <= maxJ; j++) {
            const y = gridMin2 + j * stepY;
            const diffy = y - cy;
            const termY = (diffy * diffy) * inv2SigYSq;
            const rowOffset = j * numBinsX;

            for (let i = minI; i <= maxI; i++) {
              const x = gridMin1 + i * stepX;
              const diffx = x - cx;
              const termX = (diffx * diffx) * inv2SigXSq;

              accumulatedV2D[rowOffset + i] += height * Math.exp(-(termX + termY));
            }
          }
        }

        let minFES2D = Infinity;
        const rawF2D = new Float64Array(numBinsX * numBinsY);
        for (let idx = 0; idx < numBinsX * numBinsY; idx++) {
          const val = -wtFactor * accumulatedV2D[idx];
          rawF2D[idx] = val;
          if (val < minFES2D) minFES2D = val;
        }

        const grid2DFlat = new Float64Array(numBinsX * numBinsY * 2);
        for (let idx = 0; idx < numBinsX * numBinsY; idx++) {
          grid2DFlat[idx * 2] = rawF2D[idx];
          grid2DFlat[idx * 2 + 1] = rawF2D[idx] - minFES2D;
        }

        // --- 1D Projections Calculation ---
        const kBT = 2.4943; // kJ/mol at 300K

        // 1. Projection on CV1 (integrating / minimizing over CV2 / j)
        const projCV1 = new Array(numBinsX);
        let minProjCV1_int = Infinity;
        let minProjCV1_min = Infinity;
        const rawProjCV1_int = new Float64Array(numBinsX);
        const rawProjCV1_min = new Float64Array(numBinsX);

        for (let i = 0; i < numBinsX; i++) {
          let sumExp = 0;
          let minF = Infinity;
          for (let j = 0; j < numBinsY; j++) {
            const idx = j * numBinsX + i;
            const fVal = rawF2D[idx];
            if (fVal < minF) minF = fVal;
            sumExp += Math.exp(-fVal / kBT);
          }
          const fInt = -kBT * Math.log(sumExp);
          rawProjCV1_int[i] = fInt;
          rawProjCV1_min[i] = minF;
          if (fInt < minProjCV1_int) minProjCV1_int = fInt;
          if (minF < minProjCV1_min) minProjCV1_min = minF;
        }

        for (let i = 0; i < numBinsX; i++) {
          const s1 = gridMin1 + i * stepX;
          projCV1[i] = {
            s: parseFloat(s1.toFixed(4)),
            fesInt: parseFloat((rawProjCV1_int[i] - minProjCV1_int).toFixed(4)),
            fesMin: parseFloat((rawProjCV1_min[i] - minProjCV1_min).toFixed(4)),
            rawFesInt: parseFloat(rawProjCV1_int[i].toFixed(4)),
            rawFesMin: parseFloat(rawProjCV1_min[i].toFixed(4))
          };
        }

        // 2. Projection on CV2 (integrating / minimizing over CV1 / i)
        const projCV2 = new Array(numBinsY);
        let minProjCV2_int = Infinity;
        let minProjCV2_min = Infinity;
        const rawProjCV2_int = new Float64Array(numBinsY);
        const rawProjCV2_min = new Float64Array(numBinsY);

        for (let j = 0; j < numBinsY; j++) {
          let sumExp = 0;
          let minF = Infinity;
          for (let i = 0; i < numBinsX; i++) {
            const idx = j * numBinsX + i;
            const fVal = rawF2D[idx];
            if (fVal < minF) minF = fVal;
            sumExp += Math.exp(-fVal / kBT);
          }
          const fInt = -kBT * Math.log(sumExp);
          rawProjCV2_int[j] = fInt;
          rawProjCV2_min[j] = minF;
          if (fInt < minProjCV2_int) minProjCV2_int = fInt;
          if (minF < minProjCV2_min) minProjCV2_min = minF;
        }

        for (let j = 0; j < numBinsY; j++) {
          const s2 = gridMin2 + j * stepY;
          projCV2[j] = {
            s: parseFloat(s2.toFixed(4)),
            fesInt: parseFloat((rawProjCV2_int[j] - minProjCV2_int).toFixed(4)),
            fesMin: parseFloat((rawProjCV2_min[j] - minProjCV2_min).toFixed(4)),
            rawFesInt: parseFloat(rawProjCV2_int[j].toFixed(4)),
            rawFesMin: parseFloat(rawProjCV2_min[j].toFixed(4))
          };
        }

        timelineGrids[f] = {
          frameIndex: f,
          pct: f,
          sampleTime,
          activeHillsCount: endH,
          grid2DFlat,
          projCV1,
          projCV2,
          numBinsX,
          numBinsY,
          gridMin1,
          gridMax1,
          gridMin2,
          gridMax2
        };

        if (f % 2 === 0 || f === 100) {
          self.postMessage({ progress: 50 + Math.floor((f / 100) * 50) });
        }
      }
    }

    // Pass parsedHills (or max 30,000 per walker for multiwalker) so trajectory lines stay 100% intact
    let UIHills = parsedHills;
    if (parsedHills.length > 30000) {
      const step = Math.ceil(parsedHills.length / 30000);
      UIHills = [];
      for (let i = 0; i < parsedHills.length; i += step) {
        UIHills.push(parsedHills[i]);
      }
    }

    self.postMessage({
      result: {
        headerMeta,
        fieldNames,
        cvNames,
        is2D,
        numWalkers: detectedWalkers,
        hills: UIHills,
        totalHills: totalOriginalHills,
        strideFactor: 1,
        timeRange: [startTime, endTime],
        stride: parsedHills.length > 1 ? (parsedHills[1].time - startTime) || 10 : 10,
        effectiveBiasFactor: gamma,
        wtFactor,
        timelineGrids
      }
    });
  };
  `;
  const blob = new Blob([code], { type: "application/javascript" });
  return new Worker(URL.createObjectURL(blob));
}

// --- 2D Canvas Heatmap Component ---
function Canvas2DHeatmap({
  frameData,
  energyRefMode,
  energyUnits,
  cvNames,
  hills,
  colorPalette
}) {
  const canvasRef = useRef(null);
  const [hoverInfo, setHoverInfo] = useState(null);
  const [showTrajectory, setShowTrajectory] = useState(false);
  const [useAutoCmapColor, setUseAutoCmapColor] = useState(true);
  const [customTrajectoryColor, setCustomTrajectoryColor] = useState("#00b3ff");
  const [projMode, setProjMode] = useState("int"); // "int" (Boltzmann kBT) or "min" (Minimum energy path)

  const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

  const getTrajectoryColors = (palette, autoCmap, defaultColor) => {
    if (!autoCmap) {
      return {
        line: defaultColor || "rgba(0, 179, 255, 0.9)",
        headFill: defaultColor || "#00b3ff",
        headStroke: "#ffffff",
        glow: defaultColor || "#00b3ff"
      };
    }

    switch (palette) {
      case "inferno":
        return {
          line: "rgba(0, 0, 0, 0.85)",
          headFill: "#000000",
          headStroke: "#ffffff",
          glow: "rgba(255, 255, 255, 0.8)"
        };
      case "viridis":
        return {
          line: "rgba(244, 114, 182, 0.9)",
          headFill: "#f472b6",
          headStroke: "#ffffff",
          glow: "rgba(244, 114, 182, 0.8)"
        };
      case "spectral":
        return {
          line: "rgba(15, 23, 42, 0.9)",
          headFill: "#0f172a",
          headStroke: "#ffffff",
          glow: "rgba(255, 255, 255, 0.7)"
        };
      case "plasma":
        return {
          line: "rgba(255, 255, 255, 0.95)",
          headFill: "#ffffff",
          headStroke: "#0f172a",
          glow: "rgba(255, 255, 255, 0.9)"
        };
      case "coolwarm":
        return {
          line: "rgba(15, 23, 42, 0.9)",
          headFill: "#0f172a",
          headStroke: "#ffffff",
          glow: "rgba(255, 255, 255, 0.8)"
        };
      default:
        return {
          line: "rgba(0, 179, 255, 0.9)",
          headFill: "#00b3ff",
          headStroke: "#ffffff",
          glow: "rgba(0, 179, 255, 0.8)"
        };
    }
  };

  useEffect(() => {
    if (!frameData || !frameData.grid2DFlat || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat, projCV1, projCV2 } = frameData;
    const width = canvas.width;
    const height = canvas.height;

    const padLeft = 60;
    const padRight = 145; // 80px for right 1D plot + 15px gap + 14px colorbar + text
    const padTop = 90;    // 70px for top 1D plot + 20px margin
    const padBottom = 58; // Ample clearance for X axis ticks & title

    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    ctx.clearRect(0, 0, width, height);

    ctx.fillStyle = "#090d16";
    ctx.fillRect(0, 0, width, height);

    const isZeroRef = energyRefMode !== "raw";
    let minVal = Infinity, maxVal = -Infinity;
    for (let i = 0; i < numBinsX * numBinsY; i++) {
      const v = isZeroRef ? grid2DFlat[i * 2 + 1] : grid2DFlat[i * 2];
      const scaledV = v * unitScale;
      if (scaledV < minVal) minVal = scaledV;
      if (scaledV > maxVal) maxVal = scaledV;
    }

    // --- 1. TOP 1D PROJECTION F(CV1) ---
    if (projCV1 && projCV1.length > 0) {
      const modeKey = projMode === "int" ? "fesInt" : "fesMin";
      let minF1 = Infinity, maxF1 = -Infinity;
      for (let i = 0; i < projCV1.length; i++) {
        const v = projCV1[i][modeKey];
        if (v < minF1) minF1 = v;
        if (v > maxF1) maxF1 = v;
      }
      const rangeF1 = maxF1 - minF1 || 1;

      const topY1 = 12;
      const topH = padTop - 22;
      const topY2 = topY1 + topH;

      ctx.fillStyle = "#0c1220";
      ctx.fillRect(padLeft, topY1, plotW, topH);
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      ctx.strokeRect(padLeft, topY1, plotW, topH);

      ctx.fillStyle = "#38bdf8";
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`F(${cvNames[0] || "CV1"}) 1D Projection [${projMode === "int" ? "k_BT Int" : "Min Path"}]`, padLeft + 6, topY1 + 12);

      // Area Fill
      ctx.beginPath();
      ctx.moveTo(padLeft, topY2);
      for (let i = 0; i < projCV1.length; i++) {
        const px = padLeft + (i / (projCV1.length - 1)) * plotW;
        const v = projCV1[i][modeKey];
        const norm = (v - minF1) / rangeF1;
        const py = topY2 - norm * (topH - 16);
        ctx.lineTo(px, py);
      }
      ctx.lineTo(padLeft + plotW, topY2);
      ctx.closePath();

      const gradTop = ctx.createLinearGradient(0, topY1, 0, topY2);
      gradTop.addColorStop(0, "rgba(56, 189, 248, 0.45)");
      gradTop.addColorStop(1, "rgba(2, 132, 199, 0.05)");
      ctx.fillStyle = gradTop;
      ctx.fill();

      // Stroke Line
      ctx.beginPath();
      for (let i = 0; i < projCV1.length; i++) {
        const px = padLeft + (i / (projCV1.length - 1)) * plotW;
        const v = projCV1[i][modeKey];
        const norm = (v - minF1) / rangeF1;
        const py = topY2 - norm * (topH - 16);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 1.8;
      ctx.stroke();
    }

    // --- 2. MAIN CENTER 2D HEATMAP ---
    const binPixelW = plotW / numBinsX;
    const binPixelH = plotH / numBinsY;

    for (let j = 0; j < numBinsY; j++) {
      for (let i = 0; i < numBinsX; i++) {
        const idx = j * numBinsX + i;
        const v = isZeroRef ? grid2DFlat[idx * 2 + 1] : grid2DFlat[idx * 2];
        const valScaled = v * unitScale;

        ctx.fillStyle = getHeatmapColor(valScaled, minVal, maxVal, colorPalette);
        const px = padLeft + i * binPixelW;
        const py = height - padBottom - (j + 1) * binPixelH;
        ctx.fillRect(px, py, binPixelW + 0.6, binPixelH + 0.6);
      }
    }

    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 1.5;
    ctx.strokeRect(padLeft, padTop, plotW, plotH);

    // X Axis Ticks & Grid
    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px Inter, sans-serif";
    ctx.textAlign = "center";

    const numTicksX = 5;
    for (let t = 0; t <= numTicksX; t++) {
      const frac = t / numTicksX;
      const xVal = gridMin1 + frac * (gridMax1 - gridMin1);
      const px = padLeft + frac * plotW;

      ctx.strokeStyle = "#1e293b";
      ctx.beginPath();
      ctx.moveTo(px, padTop);
      ctx.lineTo(px, padTop + plotH);
      ctx.stroke();

      ctx.strokeStyle = "#475569";
      ctx.beginPath();
      ctx.moveTo(px, padTop + plotH);
      ctx.lineTo(px, padTop + plotH + 4);
      ctx.stroke();

      ctx.fillText(xVal.toFixed(1), px, padTop + plotH + 18);
    }

    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 12px Inter, sans-serif";
    ctx.fillText(`${cvNames[0] || "CV1"} Coordinate`, padLeft + plotW / 2, height - 12);

    // Y Axis Ticks & Grid
    ctx.textAlign = "right";
    const numTicksY = 5;
    for (let t = 0; t <= numTicksY; t++) {
      const frac = t / numTicksY;
      const yVal = gridMin2 + frac * (gridMax2 - gridMin2);
      const py = height - padBottom - frac * plotH;

      ctx.strokeStyle = "#1e293b";
      ctx.beginPath();
      ctx.moveTo(padLeft, py);
      ctx.lineTo(padLeft + plotW, py);
      ctx.stroke();

      ctx.strokeStyle = "#475569";
      ctx.beginPath();
      ctx.moveTo(padLeft - 4, py);
      ctx.lineTo(padLeft, py);
      ctx.stroke();

      ctx.fillStyle = "#94a3b8";
      ctx.fillText(yVal.toFixed(2), padLeft - 8, py + 4);
    }

    ctx.save();
    ctx.translate(16, padTop + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 12px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${cvNames[1] || "CV2"} Coordinate`, 0, 0);
    ctx.restore();

    // --- 3. RIGHT 1D PROJECTION F(CV2) ---
    if (projCV2 && projCV2.length > 0) {
      const modeKey = projMode === "int" ? "fesInt" : "fesMin";
      let minF2 = Infinity, maxF2 = -Infinity;
      for (let j = 0; j < projCV2.length; j++) {
        const v = projCV2[j][modeKey];
        if (v < minF2) minF2 = v;
        if (v > maxF2) maxF2 = v;
      }
      const rangeF2 = maxF2 - minF2 || 1;

      const rightX1 = padLeft + plotW + 12;
      const rightW = 75;
      const rightX2 = rightX1 + rightW;

      ctx.fillStyle = "#0c1220";
      ctx.fillRect(rightX1, padTop, rightW, plotH);
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      ctx.strokeRect(rightX1, padTop, rightW, plotH);

      ctx.fillStyle = "#c084fc";
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`F(${cvNames[1] || "CV2"}) 1D`, rightX1 + 4, padTop - 5);

      // Area Fill
      ctx.beginPath();
      ctx.moveTo(rightX1, padTop + plotH);
      for (let j = 0; j < projCV2.length; j++) {
        const py = (padTop + plotH) - (j / (projCV2.length - 1)) * plotH;
        const v = projCV2[j][modeKey];
        const norm = (v - minF2) / rangeF2;
        const px = rightX1 + norm * (rightW - 8);
        ctx.lineTo(px, py);
      }
      ctx.lineTo(rightX1, padTop);
      ctx.closePath();

      const gradRight = ctx.createLinearGradient(rightX1, 0, rightX2, 0);
      gradRight.addColorStop(0, "rgba(192, 132, 252, 0.45)");
      gradRight.addColorStop(1, "rgba(126, 34, 206, 0.05)");
      ctx.fillStyle = gradRight;
      ctx.fill();

      // Stroke Line
      ctx.beginPath();
      for (let j = 0; j < projCV2.length; j++) {
        const py = (padTop + plotH) - (j / (projCV2.length - 1)) * plotH;
        const v = projCV2[j][modeKey];
        const norm = (v - minF2) / rangeF2;
        const px = rightX1 + norm * (rightW - 8);
        if (j === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = "#c084fc";
      ctx.lineWidth = 1.8;
      ctx.stroke();
    }

    // --- 4. COLORBAR ---
    const barX = padLeft + plotW + 98;
    const barY = padTop;
    const barW = 12;
    const barH = plotH;

    for (let py = 0; py < barH; py++) {
      const frac = 1 - py / barH;
      const valScaled = minVal + frac * (maxVal - minVal);
      ctx.fillStyle = getHeatmapColor(valScaled, minVal, maxVal, colorPalette);
      ctx.fillRect(barX, barY + py, barW, 1);
    }

    ctx.strokeStyle = "#475569";
    ctx.strokeRect(barX, barY, barW, barH);

    ctx.fillStyle = "#cbd5e1";
    ctx.font = "10px JetBrains Mono, monospace";
    ctx.textAlign = "left";

    ctx.fillText(`${maxVal.toFixed(1)}`, barX + barW + 6, barY + 10);
    ctx.fillText(`${((minVal + maxVal) / 2).toFixed(1)}`, barX + barW + 6, barY + barH / 2 + 3);
    ctx.fillText(`${minVal.toFixed(1)}`, barX + barW + 6, barY + barH);

    ctx.font = "bold 10px Inter, sans-serif";
    ctx.fillStyle = "#38bdf8";
    ctx.fillText(`F [${energyUnits}]`, barX - 10, barY - 8);

    // --- 5. TRAJECTORY OVERLAY (IF ENABLED) ---
    if (showTrajectory && hills && hills.length > 0) {
      const uiHillsCount = Math.max(1, Math.floor((frameData.pct / 100) * hills.length));
      const activeHills = hills.slice(0, uiHillsCount);
      if (activeHills.length > 0) {
        const trajColors = getTrajectoryColors(colorPalette, useAutoCmapColor, customTrajectoryColor);

        ctx.beginPath();
        ctx.strokeStyle = trajColors.line;
        ctx.lineWidth = 2;

        for (let k = 0; k < activeHills.length; k++) {
          const cv1 = activeHills[k].cvs[0];
          const cv2 = activeHills[k].cvs[1];

          const px = padLeft + ((cv1 - gridMin1) / (gridMax1 - gridMin1 || 1)) * plotW;
          const py = height - padBottom - ((cv2 - gridMin2) / (gridMax2 - gridMin2 || 1)) * plotH;

          if (k === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.stroke();

        const last = activeHills[activeHills.length - 1];
        const lastPx = padLeft + ((last.cvs[0] - gridMin1) / (gridMax1 - gridMin1 || 1)) * plotW;
        const lastPy = height - padBottom - ((last.cvs[1] - gridMin2) / (gridMax2 - gridMin2 || 1)) * plotH;

        ctx.beginPath();
        ctx.arc(lastPx, lastPy, 6, 0, Math.PI * 2);
        ctx.fillStyle = trajColors.headFill;
        ctx.shadowColor = trajColors.glow;
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.strokeStyle = trajColors.headStroke;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    // --- 6. INTERACTIVE HOVER CROSSHAIR & TARGET DOT ---
    if (hoverInfo && hoverInfo.canvasX >= padLeft && hoverInfo.canvasX <= padLeft + plotW &&
      hoverInfo.canvasY >= padTop && hoverInfo.canvasY <= padTop + plotH) {
      const hx = hoverInfo.canvasX;
      const hy = hoverInfo.canvasY;

      // Vertical crosshair (Top 1D plot through Heatmap)
      ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(hx, 12);
      ctx.lineTo(hx, padTop + plotH);
      ctx.stroke();

      // Horizontal crosshair (Heatmap into Right 1D plot)
      ctx.strokeStyle = "rgba(192, 132, 252, 0.5)";
      ctx.beginPath();
      ctx.moveTo(padLeft, hy);
      ctx.lineTo(padLeft + plotW + 87, hy);
      ctx.stroke();
      ctx.setLineDash([]); // reset line dash

      // Target Dot at exact mouse location
      ctx.beginPath();
      ctx.arc(hx, hy, 5, 0, Math.PI * 2);
      ctx.fillStyle = "#00f0ff";
      ctx.shadowColor = "#00f0ff";
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }, [frameData, energyRefMode, energyUnits, cvNames, hills, colorPalette, showTrajectory, useAutoCmapColor, customTrajectoryColor, projMode, hoverInfo]);

  const handleMouseMove = (e) => {
    if (!canvasRef.current || !frameData || !frameData.grid2DFlat) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    const padLeft = 60;
    const padRight = 145;
    const padTop = 90;
    const padBottom = 58;
    const width = canvasRef.current.width;
    const height = canvasRef.current.height;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    if (x < padLeft || x > padLeft + plotW || y < padTop || y > padTop + plotH) {
      setHoverInfo(null);
      return;
    }

    const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat, projCV1, projCV2 } = frameData;

    const normX = (x - padLeft) / plotW;
    const normY = (padTop + plotH - y) / plotH;

    const cv1Val = gridMin1 + normX * (gridMax1 - gridMin1);
    const cv2Val = gridMin2 + normY * (gridMax2 - gridMin2);

    const binI = Math.min(numBinsX - 1, Math.max(0, Math.floor(normX * numBinsX)));
    const binJ = Math.min(numBinsY - 1, Math.max(0, Math.floor(normY * numBinsY)));

    const idx = binJ * numBinsX + binI;
    const rawVal = energyRefMode !== "raw" ? grid2DFlat[idx * 2 + 1] : grid2DFlat[idx * 2];
    const fesVal = parseFloat((rawVal * unitScale).toFixed(3));

    const modeKey = projMode === "int" ? "fesInt" : "fesMin";
    const proj1Val = projCV1 && projCV1[binI] ? projCV1[binI][modeKey] : null;
    const proj2Val = projCV2 && projCV2[binJ] ? projCV2[binJ][modeKey] : null;

    setHoverInfo({
      canvasX: x,
      canvasY: y,
      cv1: cv1Val.toFixed(3),
      cv2: cv2Val.toFixed(3),
      fes: fesVal,
      proj1: proj1Val,
      proj2: proj2Val
    });
  };

  const handleExportProj = (cvIdx) => {
    if (!frameData) return;
    const projData = cvIdx === 1 ? frameData.projCV1 : frameData.projCV2;
    if (!projData || projData.length === 0) return;

    const cvName = cvNames[cvIdx - 1] || `CV${cvIdx}`;
    const modeKey = projMode === "int" ? "fesInt" : "fesMin";
    const rawModeKey = projMode === "int" ? "rawFesInt" : "rawFesMin";

    const header = [
      `#! FIELDS ${cvName} file.free`,
      `#! SET min_${cvName} ${projData[0].s}`,
      `#! SET max_${cvName} ${projData[projData.length - 1].s}`,
      `#! SET nbins_${cvName} ${projData.length}`,
      `#! SET periodic_${cvName} false`
    ].join("\n");

    const rows = projData.map(
      (p) =>
        `${p.s.toFixed(5).padStart(12)} ${(energyRefMode === "raw" ? p[rawModeKey] : p[modeKey])
          .toFixed(5)
          .padStart(14)}`
    );

    const fileContent = `${header}\n${rows.join("\n")}\n`;
    const blob = new Blob([fileContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `fes_proj_${cvName}.dat`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col items-center space-y-2.5 relative w-full">
      <div className="flex flex-wrap justify-between items-center w-full px-1 text-xs gap-2">
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer bg-slate-950/80 px-3 py-1 rounded-xl border border-slate-800 hover:border-slate-700 transition-all text-slate-300">
            <input
              type="checkbox"
              checked={showTrajectory}
              onChange={(e) => setShowTrajectory(e.target.checked)}
              className="accent-cyan-500 rounded"
            />
            <span className="font-semibold text-xs">Show Trajectory Overlay</span>
          </label>

          {showTrajectory && (
            <div className="flex items-center gap-2 bg-slate-950/80 px-2.5 py-1 rounded-xl border border-slate-800 text-slate-300 text-xs">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useAutoCmapColor}
                  onChange={(e) => setUseAutoCmapColor(e.target.checked)}
                  className="accent-indigo-500 rounded"
                />
                <span className="text-[11px] font-medium">Auto Cmap Color</span>
              </label>
              {!useAutoCmapColor && (
                <div className="flex items-center gap-1 ml-1 border-l border-slate-800 pl-2">
                  <span className="text-[10px] text-slate-400">Color:</span>
                  <input
                    type="color"
                    value={customTrajectoryColor}
                    onChange={(e) => setCustomTrajectoryColor(e.target.value)}
                    className="w-5 h-5 bg-transparent border-0 cursor-pointer rounded overflow-hidden"
                    title="Custom trajectory color"
                  />
                </div>
              )}
            </div>
          )}

          {/* Projection Mode Switch */}
          <div className="flex bg-slate-950/90 p-0.5 rounded-xl border border-slate-800 text-[11px]">
            <button
              onClick={() => setProjMode("int")}
              className={`px-2.5 py-1 rounded-lg font-bold transition-all ${projMode === "int"
                  ? "bg-cyan-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
                }`}
              title="Boltzmann integration: F(s₁) = -k_B T ln Σ exp(-F/k_B T)"
            >
              Boltzmann (k<sub>B</sub>T)
            </button>
            <button
              onClick={() => setProjMode("min")}
              className={`px-2.5 py-1 rounded-lg font-bold transition-all ${projMode === "min"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
                }`}
              title="Minimum energy path: F_min(s1) = min_s2 F(s1, s2)"
            >
              Minimum Path
            </button>
          </div>

          {/* Export Buttons */}
          <button
            onClick={() => handleExportProj(1)}
            className="px-2.5 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 rounded-xl text-[11px] font-semibold flex items-center gap-1 transition-all"
            title={`Export 1D projection for ${cvNames[0] || "CV1"} as PLUMED fes.dat`}
          >
            <Download size={12} /> Export {cvNames[0] || "CV1"} .dat
          </button>

          <button
            onClick={() => handleExportProj(2)}
            className="px-2.5 py-1 bg-purple-950 hover:bg-purple-900 text-purple-300 border border-purple-700/60 rounded-xl text-[11px] font-semibold flex items-center gap-1 transition-all"
            title={`Export 1D projection for ${cvNames[1] || "CV2"} as PLUMED fes.dat`}
          >
            <Download size={12} /> Export {cvNames[1] || "CV2"} .dat
          </button>
        </div>

        {hoverInfo ? (
          <div className="flex items-center gap-3 font-mono text-xs bg-slate-950/90 px-3 py-1 rounded-xl border border-indigo-500/40 shadow-lg">
            <span className="text-slate-300">{cvNames[0] || "CV1"}: <strong className="text-cyan-300">{hoverInfo.cv1}</strong> {hoverInfo.proj1 !== null && <span className="text-cyan-400 text-[10px]">(F₁: {hoverInfo.proj1})</span>}</span>
            <span className="text-slate-300">{cvNames[1] || "CV2"}: <strong className="text-purple-300">{hoverInfo.cv2}</strong> {hoverInfo.proj2 !== null && <span className="text-purple-400 text-[10px]">(F₂: {hoverInfo.proj2})</span>}</span>
            <span className="text-rose-400 font-bold">F 2D: {hoverInfo.fes} {energyUnits}</span>
          </div>
        ) : (
          <span className="text-[11px] text-slate-400 font-mono italic">Hover over Joint Plot for 1D/2D energy inspection</span>
        )}
      </div>

      <div className="relative border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-950 p-1.5 w-full flex justify-center">
        <canvas
          ref={canvasRef}
          width={860}
          height={480}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverInfo(null)}
          className="cursor-crosshair block rounded-xl max-w-full"
        />
      </div>
    </div>
  );
}

// --- HILLS Inspector Parameters Control Panel ---
function HillsControlPanel({
  energyRefMode,
  setEnergyRefMode,
  isWtScaling,
  setIsWtScaling,
  inputNumBins,
  setInputNumBins,
  inputCustomBias,
  setInputCustomBias,
  energyUnits,
  setEnergyUnits,
  inputGridMin,
  setInputGridMin,
  inputGridMax,
  setInputGridMax,
  handleApplyGridParams,
  handleResetGridBounds,
  hillsMetadata
}) {
  return (
    <div className="flex flex-col space-y-4 font-sans text-slate-100">
      {/* Energy Display Mode Card */}
      <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 space-y-2.5">
        <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-2">
          <Sliders size={14} className="text-indigo-400" />
          Energy Display Mode
        </h3>

        <div className="space-y-2 text-xs">
          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Bulk Plateau Reference [F(bulk) = 0]</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Sets bulk solvent energy to 0, minimum well depth is -ΔG
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeVisualizer"
              checked={energyRefMode === "plateauZero"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("plateauZero")}
              className="accent-indigo-500 mt-1"
            />
          </label>

          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Relative to Minimum [F(min) = 0]</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Sets minimum bound well to 0, bulk plateau is +ΔG
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeVisualizer"
              checked={energyRefMode === "minZero"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("minZero")}
              className="accent-indigo-500 mt-1"
            />
          </label>

          <label className="flex items-start justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all gap-2">
            <div>
              <div className="font-semibold text-slate-200 text-[11px]">Direct Absolute Potential [F(s) = -V(s)]</div>
              <div className="text-[9px] text-slate-400 mt-0.5 leading-tight">
                Raw unshifted cumulative bias potential
              </div>
            </div>
            <input
              type="radio"
              name="energyRefModeVisualizer"
              checked={energyRefMode === "raw"}
              onChange={() => setEnergyRefMode && setEnergyRefMode("raw")}
              className="accent-indigo-500 mt-1"
            />
          </label>
        </div>

        <div className="pt-1">
          <label className="flex items-center justify-between p-2 bg-slate-900 rounded-lg border border-slate-800 cursor-pointer hover:border-slate-700 transition-all text-xs">
            <span className="font-semibold text-slate-300 text-[10px]">
              Well-Tempered Scaling Factor [γ/(γ-1)]
            </span>
            <input
              type="checkbox"
              checked={isWtScaling}
              onChange={(e) => setIsWtScaling && setIsWtScaling(e.target.checked)}
              className="accent-indigo-500 rounded"
            />
          </label>
        </div>
      </div>

      {/* Grid & Calculation Settings Form */}
      <form onSubmit={handleApplyGridParams} className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-3.5 space-y-2.5 flex flex-col justify-between">
        <div>
          <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-2 mb-2">
            <Sliders size={14} className="text-indigo-400" />
            FES Grid Parameters
          </h3>

          <div className="flex flex-col space-y-2">
            {!hillsMetadata?.is2D && (
              <div>
                <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                  Grid Resolution (Bins):
                </label>
                <input
                  type="number"
                  min="50"
                  max="1000"
                  value={inputNumBins}
                  onChange={(e) => setInputNumBins && setInputNumBins(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-cyan-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>
            )}

            <div>
              <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                Bias Factor (γ):
              </label>
              <input
                type="text"
                placeholder={`Detected: ${hillsMetadata?.effectiveBiasFactor ?? 60}`}
                value={inputCustomBias}
                onChange={(e) => setInputCustomBias && setInputCustomBias(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-indigo-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-[10px] text-slate-400 mb-0.5 font-medium">
                Energy Units:
              </label>
              <select
                value={energyUnits}
                onChange={(e) => setEnergyUnits && setEnergyUnits(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none"
              >
                <option value="kJ/mol">kJ/mol</option>
                <option value="kcal/mol">kcal/mol</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-0.5">
              <div>
                <label className="block text-[9px] text-slate-400 mb-0.5 font-medium">Min CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMin}
                  onChange={(e) => setInputGridMin && setInputGridMin(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-[9px] text-slate-400 mb-0.5 font-medium">Max CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMax}
                  onChange={(e) => setInputGridMax && setInputGridMax(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-2 pt-3">
          <button
            type="submit"
            className="flex-1 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-md"
          >
            <RefreshCw size={14} /> Apply Parameters
          </button>

          <button
            type="button"
            onClick={handleResetGridBounds}
            className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 rounded-xl text-xs font-semibold"
            title="Reset Bounds"
          >
            <RotateCcw size={14} />
          </button>
        </div>
      </form>
    </div>
  );
}

function HillsVisualizerInner({
  numBins = 500,
  customBiasFactor = "",
  gridMinUser = "",
  gridMaxUser = "",
  energyUnits = "kJ/mol",
  setEnergyUnits,
  energyRefMode = "plateauZero",
  setEnergyRefMode,
  isWtScaling = true,
  setIsWtScaling,
  inputNumBins = "500",
  setInputNumBins,
  inputCustomBias = "",
  setInputCustomBias,
  inputGridMin = "",
  setInputGridMin,
  inputGridMax = "",
  setInputGridMax,
  handleApplyGridParams: propApplyGridParams,
  handleResetGridBounds: propResetGridBounds,
  hillsMetadata,
  setGridMinUser,
  setGridMaxUser,
  onMetadataLoaded
}) {
  const [hillsData, setHillsData] = useState(null);
  const [fileName, setFileName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [isDraggingFile, setIsDraggingFile] = useState(false);

  const [activeTab, setActiveTab] = useState("fes");
  const [colorPalette, setColorPalette] = useState("Inferno");
  const [showMetrics, setShowMetrics] = useState(false);

  // CV Visibility & Multi-Walker Subplot State
  const [showCV1, setShowCV1] = useState(true);
  const [showCV2, setShowCV2] = useState(true);
  const [numWalkersOverride, setNumWalkersOverride] = useState("auto");
  const [timeUnit, setTimeUnit] = useState("ns"); // Always "ns"

  // Interactive Mouse Box Zoom State
  const [refAreaLeft, setRefAreaLeft] = useState("");
  const [refAreaRight, setRefAreaRight] = useState("");

  const [timeStepProgress, setTimeStepProgress] = useState(100);
  const [isPlayingTime, setIsPlayingTime] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(60);

  const fileInputRef = useRef(null);
  const activeFileRef = useRef(null);
  const currentFileNameRef = useRef("");
  const isMounting = useRef(true);

  const handleResetGridBounds = propResetGridBounds || (() => {
    if (setInputGridMin) setInputGridMin("");
    if (setInputGridMax) setInputGridMax("");
    if (setGridMinUser) setGridMinUser("");
    if (setGridMaxUser) setGridMaxUser("");
  });
  const handleApplyGridParams = propApplyGridParams || ((e) => e?.preventDefault());

  // Mouse Drag Zoom Handlers
  const handleMouseDown = (e) => {
    if (e && e.activeLabel !== undefined && e.activeLabel !== null) {
      setRefAreaLeft(e.activeLabel);
      setRefAreaRight(e.activeLabel);
    }
  };

  const handleMouseMoveChart = (e) => {
    if (refAreaLeft && e && e.activeLabel !== undefined && e.activeLabel !== null) {
      setRefAreaRight(e.activeLabel);
    }
  };

  const handleMouseUp = () => {
    if (refAreaLeft !== "" && refAreaRight !== "" && refAreaLeft !== refAreaRight) {
      let x1 = parseFloat(refAreaLeft);
      let x2 = parseFloat(refAreaRight);
      if (!isNaN(x1) && !isNaN(x2)) {
        if (x1 > x2) [x1, x2] = [x2, x1];

        const minStr = x1.toFixed(3);
        const maxStr = x2.toFixed(3);

        if (setGridMinUser) setGridMinUser(minStr);
        if (setGridMaxUser) setGridMaxUser(maxStr);
        if (setInputGridMin) setInputGridMin(minStr);
        if (setInputGridMax) setInputGridMax(maxStr);
      }
    }
    setRefAreaLeft("");
    setRefAreaRight("");
  };

  // Drag and Drop Handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDraggingFile) setIsDraggingFile(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDraggingFile(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingFile(false);

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      processHillsFileObj(file);
    }
  };

  // Time Slider Animation Loop (Single Playback)
  useEffect(() => {
    let timer = null;
    if (isPlayingTime) {
      timer = setInterval(() => {
        setTimeStepProgress((prev) => {
          if (prev >= 100) {
            setIsPlayingTime(false);
            return 100;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlayingTime, playbackSpeed]);

  // Execute Background Web Worker Parsing & Pre-computation with Zero-Copy File Handle
  const processHillsFileObj = (fileObj) => {
    if (!fileObj) return;
    activeFileRef.current = fileObj;
    currentFileNameRef.current = fileObj.name || fileName || "HILLS";

    setErrorMsg("");
    setIsLoading(true);
    setLoadingProgress(5);
    setLoadingMsg(`Processing "${currentFileNameRef.current}" (${(fileObj.size / (1024 * 1024)).toFixed(1)} MB) in Worker...`);

    const worker = createHillsWorker();

    worker.onmessage = (e) => {
      if (e.data.progress !== undefined) {
        setLoadingProgress(e.data.progress);
      } else if (e.data.error) {
        setErrorMsg(e.data.error);
        setIsLoading(false);
        worker.terminate();
      } else if (e.data.result) {
        setHillsData(e.data.result);
        setFileName(currentFileNameRef.current);
        setIsLoading(false);
        setTimeStepProgress(100);
        setIsPlayingTime(false);
        if (onMetadataLoaded) onMetadataLoaded(e.data.result);
        worker.terminate();
      }
    };

    worker.onerror = (err) => {
      console.error("Worker error:", err);
      setErrorMsg("Error processing HILLS file in background Web Worker.");
      setIsLoading(false);
      worker.terminate();
    };

    // Pass File object directly to Worker (Zero-copy, zero main thread memory overhead)
    worker.postMessage({
      file: fileObj,
      numBins,
      isWtScaling,
      customBiasFactor,
      energyUnits,
      gridMinUser,
      gridMaxUser
    });
  };

  // Re-run computation only when APPLIED parameters change
  useEffect(() => {
    if (isMounting.current) {
      isMounting.current = false;
      return;
    }
    if (activeFileRef.current) {
      processHillsFileObj(activeFileRef.current);
    }
  }, [numBins, isWtScaling, customBiasFactor, gridMinUser, gridMaxUser]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    processHillsFileObj(file);
    e.target.value = null;
  };

  const currentFrameData = useMemo(() => {
    if (!hillsData || !hillsData.timelineGrids || hillsData.timelineGrids.length === 0) return null;
    const idx = Math.max(0, Math.min(100, timeStepProgress));
    const rawFrame = hillsData.timelineGrids[idx];
    if (!rawFrame) return null;

    if (!hillsData.is2D && rawFrame.gridPoints) {
      const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;
      let pts = rawFrame.gridPoints;

      // Filter grid points strictly to current ROI bounds if set
      const userMin = gridMinUser !== "" && !isNaN(parseFloat(gridMinUser)) ? parseFloat(gridMinUser) : -Infinity;
      const userMax = gridMaxUser !== "" && !isNaN(parseFloat(gridMaxUser)) ? parseFloat(gridMaxUser) : Infinity;

      const roiPts = pts.filter((p) => p.s >= userMin && p.s <= userMax);
      const activePts = roiPts.length > 0 ? roiPts : pts;

      // Calculate bulk plateau energy level strictly inside active ROI using sliding-window variance minimisation
      // Searches for the flattest contiguous segment (15% window) outside the minimum well neighbourhood,
      // avoiding corruption from boundary wall spikes.
      const nActive = activePts.length;
      const winSizeActive = Math.max(3, Math.round(nActive * 0.15));

      // Find global minimum index in activePts
      let minIdxActive = 0;
      let minValActive = activePts[0].rawFes;
      for (let i = 1; i < nActive; i++) {
        if (activePts[i].rawFes < minValActive) {
          minValActive = activePts[i].rawFes;
          minIdxActive = i;
        }
      }

      let bestVarActive = Infinity;
      let bestWinStartActive = Math.max(0, nActive - winSizeActive);

      for (let i = 0; i <= nActive - winSizeActive; i++) {
        let sum = 0;
        for (let j = i; j < i + winSizeActive; j++) sum += activePts[j].rawFes;
        const mean = sum / winSizeActive;

        let varAcc = 0;
        for (let j = i; j < i + winSizeActive; j++) {
          const d = activePts[j].rawFes - mean;
          varAcc += d * d;
        }
        const variance = varAcc / winSizeActive;

        const containsMin = minIdxActive >= i && minIdxActive < i + winSizeActive;
        if (!containsMin && variance < bestVarActive) {
          bestVarActive = variance;
          bestWinStartActive = i;
        }
      }

      if (bestVarActive === Infinity) {
        bestWinStartActive = Math.max(0, nActive - winSizeActive);
      }

      const plateauPts = activePts.slice(bestWinStartActive, bestWinStartActive + winSizeActive);
      let bulkSum = 0;
      let bulkSumX = 0;
      for (let b = 0; b < plateauPts.length; b++) {
        bulkSum += plateauPts[b].rawFes;
        bulkSumX += plateauPts[b].s;
      }
      const bulkFes = plateauPts.length > 0 ? bulkSum / plateauPts.length : activePts[activePts.length - 1].rawFes;
      const bulkS = plateauPts.length > 0 ? bulkSumX / plateauPts.length : activePts[activePts.length - 1].s;

      let minVal = Infinity;
      let minS_val = activePts[0].s;

      const formattedPoints = activePts.map((p) => {
        let val = p.rawFes;
        if (energyRefMode === "minZero") {
          val = p.zeroFes;
        } else if (energyRefMode === "plateauZero") {
          val = p.rawFes - bulkFes;
        }

        const scaledFes = parseFloat((val * unitScale).toFixed(3));
        if (scaledFes < minVal) {
          minVal = scaledFes;
          minS_val = p.s;
        }

        return {
          s: p.s,
          fes: scaledFes,
          vBias: parseFloat((p.vBiasRaw * unitScale).toFixed(3))
        };
      });

      return {
        ...rawFrame,
        gridPoints: formattedPoints,
        bulkS: parseFloat(bulkS.toFixed(3)),
        minS_val: parseFloat(minS_val.toFixed(3)),
        minVal: parseFloat(minVal.toFixed(3)),
        bulkFesScaled: parseFloat((bulkFes * unitScale).toFixed(3))
      };
    }

    return rawFrame;
  }, [hillsData, timeStepProgress, energyRefMode, energyUnits, gridMinUser, gridMaxUser]);

  // Unique Integer X Ticks array for Recharts AreaChart
  const xAxisTicks = useMemo(() => {
    if (!currentFrameData?.gridPoints || currentFrameData.gridPoints.length === 0) return undefined;
    const pts = currentFrameData.gridPoints;
    const minS = Math.floor(pts[0].s);
    const maxS = Math.ceil(pts[pts.length - 1].s);
    const range = maxS - minS;
    if (range <= 0) return undefined;

    const ticks = [];
    const step = range <= 15 ? 1 : Math.ceil(range / 10);
    for (let val = minS; val <= maxS; val += step) {
      ticks.push(val);
    }
    return ticks;
  }, [currentFrameData]);

  const chartHeightData = useMemo(() => {
    if (!hillsData || !hillsData.hills) return [];
    return downsampleArray(hillsData.hills, 800);
  }, [hillsData]);

  const walkerParsedData = useMemo(() => {
    if (!hillsData || !hillsData.hills || hillsData.hills.length === 0) {
      return { numWalkers: 1, walkerSeries: [] };
    }

    const hills = hillsData.hills;

    // 1. Count initial consecutive hills sharing the same initial timestamp
    let initialSameTimeCount = 0;
    if (hills.length > 0) {
      const t0Rounded = Math.round(hills[0].time * 100) / 100;
      while (
        initialSameTimeCount < hills.length &&
        Math.round(hills[initialSameTimeCount].time * 100) / 100 === t0Rounded
      ) {
        initialSameTimeCount++;
      }
    }

    // 2. Check for timestamp drops (consecutive blocks per walker)
    const blockStartIndices = [0];
    for (let i = 1; i < hills.length; i++) {
      if (hills[i].time < hills[i - 1].time) {
        blockStartIndices.push(i);
      }
    }

    let detectedWalkers = hillsData.numWalkers || (blockStartIndices.length > 1 ? blockStartIndices.length : (initialSameTimeCount >= 2 ? initialSameTimeCount : 1));
    if (!detectedWalkers || isNaN(detectedWalkers) || detectedWalkers < 1) detectedWalkers = 1;

    const numWalkers = detectedWalkers;

    let seriesList = Array.from({ length: numWalkers }, () => []);

    if (numWalkers === 1) {
      seriesList = [hills];
    } else if (blockStartIndices.length === numWalkers && blockStartIndices.length > 1) {
      for (let w = 0; w < blockStartIndices.length; w++) {
        const start = blockStartIndices[w];
        const end = w + 1 < blockStartIndices.length ? blockStartIndices[w + 1] : hills.length;
        seriesList.push(hills.slice(start, end));
      }
    } else {
      for (let i = 0; i < hills.length; i++) {
        const h = hills[i];
        let wIdx = 0;
        if (h.walkerId !== undefined) {
          wIdx = Math.min(numWalkers - 1, Math.max(0, h.walkerId - 1));
        } else {
          wIdx = i % numWalkers;
        }
        seriesList[wIdx].push(h);
      }
    }

    // Convert each walker's hills array into chart data points downsampled for performance
    const walkerSeries = seriesList.map((wHills, wIdx) => {
      const formatted = wHills.map((h) => ({
        time: parseFloat((h.time / 1000).toFixed(4)),
        cv1: h.cvs[0],
        cv2: hillsData.is2D ? h.cvs[1] : undefined
      }));
      const downsampled = downsampleArray(formatted, 800);

      // Compute Y-domain based on visible CVs for this specific walker
      let minY = Infinity;
      let maxY = -Infinity;
      for (let i = 0; i < downsampled.length; i++) {
        const pt = downsampled[i];
        if (showCV1 && typeof pt.cv1 === "number" && !isNaN(pt.cv1)) {
          if (pt.cv1 < minY) minY = pt.cv1;
          if (pt.cv1 > maxY) maxY = pt.cv1;
        }
        if (hillsData.is2D && showCV2 && typeof pt.cv2 === "number" && !isNaN(pt.cv2)) {
          if (pt.cv2 < minY) minY = pt.cv2;
          if (pt.cv2 > maxY) maxY = pt.cv2;
        }
      }

      if (minY === Infinity) {
        minY = 0;
        maxY = 1;
      } else if (minY === maxY) {
        minY -= 1;
        maxY += 1;
      } else {
        const pad = (maxY - minY) * 0.06;
        minY = parseFloat((minY - pad).toFixed(3));
        maxY = parseFloat((maxY + pad).toFixed(3));
      }

      return {
        walkerId: wIdx + 1,
        data: downsampled,
        domainY: [minY, maxY],
        totalHills: wHills.length
      };
    });

    return { numWalkers, walkerSeries };
  }, [hillsData, showCV1, showCV2, timeUnit]);

  const stats = useMemo(() => {
    if (!hillsData || !hillsData.hills || hillsData.hills.length === 0) return null;
    const hills = hillsData.hills;

    const initialHeight = hills[0].height;
    const finalHeight = hills[hills.length - 1].height;
    const heightReductionRatio =
      initialHeight > 0
        ? (((initialHeight - finalHeight) / initialHeight) * 100).toFixed(1)
        : "0.0";

    const cv1Vals = hills.map((h) => h.cvs[0]);
    const { min: minCV1, max: maxCV1 } = getMinMax(cv1Vals, 0);

    let cv2Info = null;
    if (hillsData.is2D) {
      const cv2Vals = hills.map((h) => h.cvs[1]);
      const { min: minCV2, max: maxCV2 } = getMinMax(cv2Vals, 0);
      cv2Info = {
        name: hillsData.cvNames[1] || "CV2",
        min: minCV2.toFixed(3),
        max: maxCV2.toFixed(3)
      };
    }

    return {
      totalHills: hillsData.totalHills,
      totalTime: hillsData.timeRange[1].toFixed(1),
      stride: hillsData.stride.toFixed(1),
      initialHeight: initialHeight.toFixed(3),
      finalHeight: finalHeight.toFixed(3),
      heightReductionRatio,
      minCV1: minCV1.toFixed(3),
      maxCV1: maxCV1.toFixed(3),
      cv1Name: hillsData.cvNames[0] || "CV1",
      cv2Info,
      is2D: hillsData.is2D,
      isWT: hillsData.effectiveBiasFactor > 1
    };
  }, [hillsData]);

  const handleExportPNG = () => {
    if (!currentFrameData || !hillsData || !currentFrameData.gridPoints) return;
    export1DPlot({
      gridPoints: currentFrameData.gridPoints,
      cvName: hillsData.cvNames[0] || "D.z",
      energyUnits,
      energyRefMode,
      format: "png",
      transparent: false
    });
  };

  const handleExportFES = () => {
    if (!currentFrameData || !hillsData) return;

    if (!hillsData.is2D && currentFrameData.gridPoints) {
      const header = [
        `#! FIELDS ${hillsData.cvNames[0] || "CV1"} file.free ${hillsData.cvNames[0] || "CV1"}_der`,
        `#! SET min_${hillsData.cvNames[0] || "CV1"} ${currentFrameData.gridPoints[0].s}`,
        `#! SET max_${hillsData.cvNames[0] || "CV1"} ${currentFrameData.gridPoints[currentFrameData.gridPoints.length - 1].s}`,
        `#! SET nbins_${hillsData.cvNames[0] || "CV1"} ${numBins}`,
        `#! SET periodic_${hillsData.cvNames[0] || "CV1"} false`,
        `#! Reconstructed with Metadynamics Laboratory HILLS Inspector`,
        `#! Energy Unit: ${energyUnits}`,
        `#! Energy Reference Mode: ${energyRefMode}`
      ].join("\n");

      const lines = currentFrameData.gridPoints.map((p) => `  ${p.s}   ${p.fes}   0.0000`);
      const content = header + "\n" + lines.join("\n");

      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `fes_${hillsData.cvNames[0] || "CV1"}_1D.dat`;
      link.click();
      URL.revokeObjectURL(url);
    } else if (hillsData.is2D && currentFrameData.grid2DFlat) {
      const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat } = currentFrameData;
      const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

      const header = [
        `#! FIELDS ${hillsData.cvNames[0] || "CV1"} ${hillsData.cvNames[1] || "CV2"} file.free ${hillsData.cvNames[0] || "CV1"}_der ${hillsData.cvNames[1] || "CV2"}_der`,
        `#! SET min_${hillsData.cvNames[0] || "CV1"} ${gridMin1}`,
        `#! SET max_${hillsData.cvNames[0] || "CV1"} ${gridMax1}`,
        `#! SET nbins_${hillsData.cvNames[0] || "CV1"} ${numBinsX}`,
        `#! SET min_${hillsData.cvNames[1] || "CV2"} ${gridMin2}`,
        `#! SET max_${hillsData.cvNames[1] || "CV2"} ${gridMax2}`,
        `#! SET nbins_${hillsData.cvNames[1] || "CV2"} ${numBinsY}`,
        `#! Reconstructed 2D FES with Metadynamics Laboratory`,
        `#! Energy Unit: ${energyUnits}`
      ].join("\n");

      const stepX = (gridMax1 - gridMin1) / (numBinsX - 1);
      const stepY = (gridMax2 - gridMin2) / (numBinsY - 1);

      const lines = [];
      for (let j = 0; j < numBinsY; j++) {
        const y = gridMin2 + j * stepY;
        for (let i = 0; i < numBinsX; i++) {
          const x = gridMin1 + i * stepX;
          const idx = j * numBinsX + i;
          const rawVal = energyRefMode !== "raw" ? grid2DFlat[idx * 2 + 1] : grid2DFlat[idx * 2];
          const valScaled = (rawVal * unitScale).toFixed(4);
          lines.push(`  ${x.toFixed(4)}   ${y.toFixed(4)}   ${valScaled}   0.0000   0.0000`);
        }
        lines.push("");
      }

      const content = header + "\n" + lines.join("\n");
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `fes_2D_${hillsData.cvNames[0] || "CV1"}_${hillsData.cvNames[1] || "CV2"}.dat`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="flex flex-col w-full relative min-h-[75vh] space-y-6"
    >
      {/* Drag and Drop Hover Overlay */}
      {isDraggingFile && (
        <div className="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex flex-col items-center justify-center border-4 border-dashed border-cyan-400 rounded-3xl m-4 transition-all">
          <div className="p-8 bg-slate-900/90 border border-slate-800 rounded-3xl shadow-2xl flex flex-col items-center space-y-4 text-center max-w-md pointer-events-none">
            <div className="p-4 bg-cyan-500/20 border border-cyan-500/30 rounded-2xl text-cyan-400">
              <Upload size={48} className="animate-bounce" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Drop your HILLS file here</h2>
              <p className="text-xs text-slate-400 mt-1">
                Supports 1D and 2D PLUMED HILLS output files
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Background Web Worker Loading Spinner & Progress Bar */}
      {isLoading && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex flex-col items-center justify-center space-y-4">
          <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col items-center space-y-4 max-w-md text-center">
            <Loader2 size={40} className="text-cyan-400 animate-spin" />
            <div>
              <h3 className="font-bold text-white text-base">Processing HILLS File</h3>
              <p className="text-xs text-slate-400 mt-1 font-mono">{loadingMsg}</p>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-950 h-2 rounded-full border border-slate-800 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full transition-all duration-150"
                style={{ width: `${loadingProgress}%` }}
              ></div>
            </div>
            <span className="text-xs font-mono text-cyan-400 font-bold">{loadingProgress}%</span>
          </div>
        </div>
      )}

      {/* Top Banner Header */}
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 relative overflow-hidden">
        <div className="flex items-center gap-4 z-10">
          <div className="p-3 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border border-indigo-500/30 rounded-xl text-indigo-400 shadow-lg shadow-indigo-500/10">
            <BarChart2 size={28} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-extrabold text-white tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
                PLUMED HILLS Visualizer & Inspector
              </h1>
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-950 text-indigo-400 border border-indigo-800/60 rounded-full">
                {hillsData?.is2D ? "2D Mode Enabled" : "1D / 2D Engine"}
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              Reconstruction of 1D and 2D Free Energy Surfaces from PLUMED HILLS data
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end z-10">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current.click()}
            disabled={isLoading}
            className="py-2.5 px-5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
          >
            <Upload size={16} />
            <span>Upload HILLS File</span>
          </button>
        </div>
      </header>

      {/* Error notification banner */}
      {errorMsg && (
        <div className="bg-red-950/80 border border-red-800 text-red-200 p-4 rounded-xl text-xs flex justify-between items-center">
          <span>⚠️ Error: {errorMsg}</span>
          <button
            onClick={() => setErrorMsg("")}
            className="text-red-400 hover:text-white font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main 2-Column Inspector Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        {/* Column 2 (Adjacent to main sidebar): HILLS Inspector Options & Parameters */}
        {hillsData && (
          <div className="lg:col-span-3 space-y-4">
            <HillsControlPanel
              energyRefMode={energyRefMode}
              setEnergyRefMode={setEnergyRefMode}
              isWtScaling={isWtScaling}
              setIsWtScaling={setIsWtScaling}
              inputNumBins={inputNumBins}
              setInputNumBins={setInputNumBins}
              inputCustomBias={inputCustomBias}
              setInputCustomBias={setInputCustomBias}
              energyUnits={energyUnits}
              setEnergyUnits={setEnergyUnits}
              inputGridMin={inputGridMin}
              setInputGridMin={setInputGridMin}
              inputGridMax={inputGridMax}
              setInputGridMax={setInputGridMax}
              handleApplyGridParams={handleApplyGridParams}
              handleResetGridBounds={handleResetGridBounds}
              hillsMetadata={hillsMetadata}
            />
          </div>
        )}

        {/* Column 3 (Rest of the screen): File Upload Dropzone / Visualizer Content */}
        <div className={hillsData ? "lg:col-span-9 space-y-4" : "lg:col-span-12 space-y-4"}>

          {/* EMPTY STATE PLACEHOLDER (When no HILLS file is loaded) */}
          {!hillsData && !isLoading && (
            <div className="bg-slate-900/90 backdrop-blur-xl border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-6 shadow-2xl transition-all">
              <div className="p-5 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border border-indigo-500/30 rounded-2xl text-indigo-400 shadow-xl shadow-indigo-500/10">
                <Upload size={48} className="animate-pulse" />
              </div>
              <div className="max-w-md space-y-2">
                <h2 className="text-xl font-extrabold text-white">HILLS File Visualizer (PLUMED 1D & 2D)</h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Drag your <code className="text-cyan-300 bg-slate-950 px-1.5 py-0.5 rounded font-mono">HILLS</code> file (1D or 2D) directly onto this window or click the button below to select it from your computer.
                </p>
              </div>

              <button
                onClick={() => fileInputRef.current?.click()}
                className="py-3 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-2xl text-xs font-bold flex items-center gap-2.5 transition-all shadow-xl shadow-indigo-600/25 hover:scale-105"
              >
                <Upload size={18} />
                <span>Select HILLS File</span>
              </button>
            </div>
          )}

          {/* Key Metrics Cards Dashboard (Collapsible) */}
          {stats && showMetrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Layers size={13} className="text-indigo-400" /> Gaussian Hills
                </span>
                <span className="text-xl font-extrabold text-white mt-1 font-mono">
                  {stats.totalHills}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5 font-mono">
                  {hillsData?.strideFactor > 1
                    ? `Subsampled 1:${hillsData.strideFactor} (${hillsData.hills.length.toLocaleString()} active)`
                    : (stats.is2D ? "2D Gaussian Hills" : "1D Gaussian Hills")}
                </span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Clock size={13} className="text-cyan-400" /> Total Time
                </span>
                <span className="text-xl font-extrabold text-cyan-300 mt-1 font-mono">
                  {stats.totalTime} <span className="text-xs font-sans text-slate-400">ps</span>
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">Stride τ: {stats.stride} ps</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Activity size={13} className="text-emerald-400" /> {stats.is2D ? "Collective Variables" : "Collective Variable"}
                </span>
                <span className="text-sm font-bold text-emerald-300 mt-1 font-mono truncate">
                  {stats.is2D ? `${stats.cv1Name}, ${stats.cv2Info.name}` : stats.cv1Name}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5 font-mono truncate">
                  {stats.is2D ? `[${stats.minCV1}, ${stats.maxCV1}] × [${stats.cv2Info.min}, ${stats.cv2Info.max}]` : `[${stats.minCV1}, ${stats.maxCV1}]`}
                </span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp size={13} className="text-purple-400" /> Initial Height W₀
                </span>
                <span className="text-xl font-extrabold text-purple-300 mt-1 font-mono">
                  {stats.initialHeight}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">kJ/mol per hill</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Zap size={13} className="text-amber-400" /> Final Height W_t
                </span>
                <span className="text-xl font-extrabold text-amber-300 mt-1 font-mono">
                  {stats.finalHeight}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">
                  Reduction: <span className="text-amber-400 font-bold">-{stats.heightReductionRatio}%</span>
                </span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
                <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                  <Award size={13} className="text-cyan-400" /> Well-Tempered
                </span>
                <span className="text-lg font-bold text-cyan-300 mt-1">
                  {stats.isWT ? `γ = ${hillsData?.effectiveBiasFactor}` : "Standard"}
                </span>
                <span className="text-[10px] text-slate-500 mt-0.5">
                  Scale factor: {hillsData?.wtFactor?.toFixed(2)}x
                </span>
              </div>

            </div>
          )}

          {/* Navigation Tabs Header */}
          {hillsData && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-2 shadow-xl flex flex-wrap justify-between items-center gap-2">
              <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                <button
                  onClick={() => setActiveTab("fes")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${activeTab === "fes"
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <TrendingUp size={15} /> Free Energy Surface F(s)
                </button>

                <button
                  onClick={() => setActiveTab("height")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${activeTab === "height"
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <Zap size={15} /> Height Decay W(t)
                </button>

                <button
                  onClick={() => setActiveTab("cv")}
                  className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${activeTab === "cv"
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  <Activity size={15} /> CV Trajectory s(t)
                </button>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowMetrics(!showMetrics)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-950/80 hover:bg-slate-800 text-slate-300 border border-slate-800 rounded-xl text-xs font-semibold transition-all shadow-sm"
                  title="Toggle 6-metric summary cards bar"
                >
                  <BarChart2 size={13} className="text-cyan-400" />
                  <span>{showMetrics ? "Hide Metrics" : "Show Metrics"}</span>
                </button>

                {/* File Name Tag */}
                <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
                  <FileText size={14} className="text-indigo-400" />
                  <span>{fileName || "No file loaded"}</span>
                </div>
              </div>
            </div>
          )}

          {/* MAIN TAB CONTENT */}
          {hillsData && activeTab === "fes" && currentFrameData && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-2xl space-y-3.5 w-full">

              <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-2">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <TrendingUp size={20} className="text-indigo-400" />
                    {hillsData.is2D ? "Reconstructed 2D Free Energy Heatmap F(s₁, s₂)" : "Reconstructed Free Energy Profile F(s)"}
                  </h2>
                  <p className="text-slate-400 text-xs mt-0.5">
                    {hillsData.is2D
                      ? "2D Free Energy Surface reconstructed from 2D Gaussian HILLS summation"
                      : "Click and drag across the chart to select a vertical zoom region (ROI) for export"}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {!hillsData.is2D && (gridMinUser || gridMaxUser) && (
                    <div className="flex items-center gap-2 bg-cyan-950/90 border border-cyan-600/70 px-3 py-1 rounded-xl text-xs text-cyan-300 font-mono shadow-sm">
                      <ZoomIn size={14} className="text-cyan-400 animate-pulse" />
                      <span>ROI: [{gridMinUser || "Min"}, {gridMaxUser || "Max"}]</span>
                      <button
                        onClick={handleResetGridBounds}
                        className="ml-1 text-slate-400 hover:text-white font-bold p-0.5 rounded"
                        title="Reset Zoom / Clear ROI"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  )}

                  {hillsData.is2D && (
                    <select
                      value={colorPalette}
                      onChange={(e) => setColorPalette(e.target.value)}
                      className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl px-2.5 py-1.5 outline-none font-medium"
                    >
                      <option value="Inferno">Inferno (Thermal Glow)</option>
                      <option value="Viridis">Viridis (Scientific)</option>
                      <option value="Spectral">Spectral (Rainbow)</option>
                      <option value="CoolWarm">Cool-Warm (Blue-Red)</option>
                    </select>
                  )}

                  {/* Direct Clean Export PNG Button */}
                  {!hillsData.is2D && (
                    <button
                      onClick={handleExportPNG}
                      className="px-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                      title="Export 1D PMF Plot as PNG"
                    >
                      <ImageIcon size={14} /> Export PNG
                    </button>
                  )}

                  <button
                    onClick={handleExportFES}
                    className="px-3 py-1.5 bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/60 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                    title="Export PLUMED-compatible fes.dat file"
                  >
                    <Download size={14} /> Export fes.dat
                  </button>
                </div>
              </div>

              {/* Time Trajectory Progress Slider with Smooth REAL-TIME PLAY / PAUSE */}
              <div className="bg-slate-950/80 border border-slate-800/80 p-3 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        if (!isPlayingTime && timeStepProgress >= 100) {
                          setTimeStepProgress(0);
                        }
                        setIsPlayingTime(!isPlayingTime);
                      }}
                      className={`py-1 px-3 rounded-lg font-bold text-xs shadow-md flex items-center gap-1.5 transition-all ${isPlayingTime
                        ? "bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20"
                        : "bg-emerald-500 text-slate-950 hover:bg-emerald-400 shadow-emerald-500/20"
                        }`}
                    >
                      {isPlayingTime ? <><Pause size={13} /> PAUSE</> : <><Play size={13} /> PLAY</>}
                    </button>

                    <button
                      onClick={() => setTimeStepProgress(0)}
                      className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 rounded-lg border border-slate-800"
                      title="Reset to 0% (Flat t=0)"
                    >
                      <RotateCcw size={13} />
                    </button>
                  </div>

                  <span className="font-mono text-cyan-400 font-bold text-xs">
                    {timeStepProgress}% (t = {currentFrameData.sampleTime.toFixed(1)} ps • {currentFrameData.activeHillsCount} hills)
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={timeStepProgress}
                    onChange={(e) => setTimeStepProgress(parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                </div>

                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>0 ps (0% - Flat)</span>
                  <span>50%</span>
                  <span>{hillsData.timeRange[1].toFixed(0)} ps (End)</span>
                </div>
              </div>

              {/* FULL-WIDTH 1D AreaChart vs 2D Heatmap Canvas */}
              {!hillsData.is2D ? (
                <div className="h-[340px] w-full pt-1 select-none">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={currentFrameData.gridPoints}
                      margin={{ top: 15, right: 25, left: 10, bottom: 20 }}
                      onMouseDown={handleMouseDown}
                      onMouseMove={handleMouseMoveChart}
                      onMouseUp={handleMouseUp}
                    >
                      <defs>
                        <linearGradient id="fesGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.65} />
                          <stop offset="95%" stopColor="#dc2626" stopOpacity={0.1} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis
                        dataKey="s"
                        type="number"
                        domain={['dataMin', 'dataMax']}
                        ticks={xAxisTicks}
                        stroke="#64748b"
                        tick={{ fill: "#94a3b8", fontSize: 12 }}
                        label={{
                          value: `Collective Variable (${hillsData.cvNames[0] || "CV1"})`,
                          position: "insideBottom",
                          offset: -12,
                          fill: "#cbd5e1",
                          fontSize: 13
                        }}
                      />
                      <YAxis
                        stroke="#64748b"
                        tick={{ fill: "#94a3b8", fontSize: 12 }}
                        domain={['auto', 'auto']}
                        label={{
                          value: `Free Energy F(s) [${energyUnits}]`,
                          angle: -90,
                          position: "insideLeft",
                          offset: 10,
                          fill: "#cbd5e1",
                          fontSize: 13
                        }}
                      />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload;
                            return (
                              <div className="bg-slate-950/95 backdrop-blur-md border border-slate-800 p-3 rounded-xl shadow-2xl text-xs space-y-1">
                                <div className="font-mono text-cyan-400 font-bold border-b border-slate-800 pb-1">
                                  {hillsData.cvNames[0] || "CV"}: {data.s}
                                </div>
                                <div className="text-rose-300 font-semibold">
                                  F(s): {data.fes} {energyUnits}
                                </div>
                                <div className="text-slate-400 font-mono text-[10px]">
                                  V_bias: {data.vBias}
                                </div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />

                      <Area
                        type="monotone"
                        dataKey="fes"
                        name="Free Energy F(s)"
                        stroke="#f87171"
                        strokeWidth={2.8}
                        fill="url(#fesGradient)"
                        isAnimationActive={false}
                      />

                      {/* Interactive Mouse Drag Selection Box */}
                      {refAreaLeft && refAreaRight ? (
                        <ReferenceArea
                          x1={refAreaLeft}
                          x2={refAreaRight}
                          strokeOpacity={0.8}
                          stroke="#38bdf8"
                          fill="#0284c7"
                          fillOpacity={0.35}
                        />
                      ) : null}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <Canvas2DHeatmap
                  frameData={currentFrameData}
                  energyRefMode={energyRefMode}
                  energyUnits={energyUnits}
                  cvNames={hillsData.cvNames}
                  hills={hillsData.hills}
                  colorPalette={colorPalette}
                />
              )}

            </div>
          )}

          {/* TAB 2: Gaussian Height Decay W(t) */}
          {hillsData && activeTab === "height" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4 w-full">
              <div className="border-b border-slate-800 pb-3">
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Zap size={18} className="text-amber-400" />
                  Gaussian Height Decay W(t) (WT-Metadynamics)
                </h2>
                <p className="text-slate-400 text-xs">
                  Evolution of deposited hill heights across the simulation
                </p>
              </div>

              <div className="h-[500px] w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartHeightData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{ value: "Simulation Time (ps)", position: "insideBottom", offset: -12, fill: "#cbd5e1", fontSize: 12 }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{ value: "Gaussian Height W(t)", angle: -90, position: "insideLeft", offset: 10, fill: "#cbd5e1", fontSize: 12 }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-xl shadow-xl text-xs space-y-1">
                              <div className="text-amber-400 font-mono font-bold">t = {d.time} ps</div>
                              <div className="text-white font-semibold">Height W: {d.height}</div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="height"
                      name="Gaussian Height W(t)"
                      stroke="#fbbf24"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* TAB 3: Collective Variable Trajectory s(t) & Multi-Walker Subplots */}
          {hillsData && activeTab === "cv" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4 w-full">
              <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-3">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Activity size={18} className="text-emerald-400" />
                    {hillsData.is2D ? "Collective Variables Trajectory (CV1, CV2) Over Time" : "Collective Variable Trajectory s(t) Over Time"}
                  </h2>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Shows system diffusion along reaction coordinate(s). Multi-walker HILLS are split into subplots.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* CV Toggles */}
                  <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800 text-xs">
                    <button
                      onClick={() => setShowCV1(!showCV1)}
                      className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1.5 transition-all text-xs ${
                        showCV1
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm"
                          : "text-slate-500 hover:text-slate-300 border border-transparent"
                      }`}
                      title="Toggle CV1 Visibility"
                    >
                      {showCV1 ? <Eye size={13} className="text-emerald-400" /> : <EyeOff size={13} />}
                      <span>{hillsData.cvNames[0] || "CV1"}</span>
                    </button>

                    {hillsData.is2D && (
                      <button
                        onClick={() => setShowCV2(!showCV2)}
                        className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1.5 transition-all text-xs ${
                          showCV2
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/50 shadow-sm"
                            : "text-slate-500 hover:text-slate-300 border border-transparent"
                        }`}
                        title="Toggle CV2 Visibility"
                      >
                        {showCV2 ? <Eye size={13} className="text-purple-400" /> : <EyeOff size={13} />}
                        <span>{hillsData.cvNames[1] || "CV2"}</span>
                      </button>
                    )}
                  </div>

                  {/* Walkers Badge */}
                  <div className="flex items-center gap-1.5 bg-slate-950/80 px-2.5 py-1 rounded-xl border border-slate-800 text-xs text-slate-300 font-mono">
                    <Users size={14} className={walkerParsedData.numWalkers > 1 ? "text-indigo-400" : "text-emerald-400"} />
                    <span className="text-[11px] font-medium text-slate-400">Walkers:</span>
                    <span className={`font-bold ${walkerParsedData.numWalkers > 1 ? "text-indigo-300" : "text-emerald-300"}`}>
                      {walkerParsedData.numWalkers} {walkerParsedData.numWalkers === 1 ? "Walker" : "Walkers"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Subplots Container - Matrix Grid (e.g. 4x4 for 16 walkers) */}
              <div className={`grid gap-4 w-full ${
                walkerParsedData.numWalkers === 16
                  ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-4"
                  : walkerParsedData.numWalkers === 9
                  ? "grid-cols-1 sm:grid-cols-3 md:grid-cols-3"
                  : walkerParsedData.numWalkers === 4
                  ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-2"
                  : walkerParsedData.numWalkers > 1
                  ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
                  : "grid-cols-1"
              }`}>
                {walkerParsedData.walkerSeries.map((wObj) => (
                  <div
                    key={wObj.walkerId}
                    className="bg-slate-950/80 border border-slate-800/90 p-3 rounded-xl space-y-1 shadow-lg flex flex-col justify-between"
                  >
                    <div className="flex justify-between items-center border-b border-slate-800/80 pb-1 text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-700/60 rounded-lg font-bold font-mono text-[11px]">
                          Walker {wObj.walkerId}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {wObj.totalHills} pts
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Y: [{wObj.domainY[0]}, {wObj.domainY[1]}]
                      </span>
                    </div>

                    <div className={
                      walkerParsedData.numWalkers >= 9
                        ? "h-[220px] w-full pt-1"
                        : walkerParsedData.numWalkers >= 4
                        ? "h-[260px] w-full pt-1"
                        : walkerParsedData.numWalkers > 1
                        ? "h-[280px] w-full pt-1"
                        : "h-[450px] w-full pt-1"
                    }>
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={wObj.data} margin={{ top: 5, right: 10, left: -15, bottom: 15 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis
                            dataKey="time"
                            stroke="#64748b"
                            tick={{ fill: "#94a3b8", fontSize: 10 }}
                            label={{ value: "Time (ns)", position: "insideBottom", offset: -10, fill: "#cbd5e1", fontSize: 10 }}
                          />
                          <YAxis
                            stroke="#64748b"
                            tick={{ fill: "#94a3b8", fontSize: 10 }}
                            domain={wObj.domainY}
                          />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const d = payload[0].payload;
                                return (
                                  <div className="bg-slate-950/95 border border-slate-800 p-2 rounded-xl shadow-2xl text-[11px] space-y-1 font-mono">
                                    <div className="text-cyan-400 font-bold border-b border-slate-800 pb-0.5">
                                      Walker {wObj.walkerId} • {d.time} ns
                                    </div>
                                    {showCV1 && (
                                      <div className="text-emerald-300 font-semibold">
                                        {hillsData.cvNames[0] || "CV1"}: {d.cv1}
                                      </div>
                                    )}
                                    {hillsData.is2D && showCV2 && typeof d.cv2 === "number" && (
                                      <div className="text-purple-300 font-semibold">
                                        {hillsData.cvNames[1] || "CV2"}: {d.cv2}
                                      </div>
                                    )}
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Legend verticalAlign="top" height={25} wrapperStyle={{ fontSize: "11px" }} />

                          {showCV1 && (
                            <Line
                              type="monotone"
                              dataKey="cv1"
                              name={hillsData.cvNames[0] || "CV1"}
                              stroke="#34d399"
                              strokeWidth={1.5}
                              dot={false}
                              isAnimationActive={false}
                            />
                          )}

                          {hillsData.is2D && showCV2 && (
                            <Line
                              type="monotone"
                              dataKey="cv2"
                              name={hillsData.cvNames[1] || "CV2"}
                              stroke="#c084fc"
                              strokeWidth={1.5}
                              dot={false}
                              isAnimationActive={false}
                            />
                          )}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default function HillsVisualizer(props) {
  return (
    <HillsErrorBoundary>
      <HillsVisualizerInner {...props} />
    </HillsErrorBoundary>
  );
}

EOF

echo "=== Writing src/sampleHills.js ==="
cat << 'EOF' > src/sampleHills.js
export const SAMPLE_HILLS_TEXT = '#! FIELDS time D sigma_D height biasf\n#! SET multivariate false\n#! SET kerneltype stretched-gaussian\n      9.999995000000002      1.925192369640072                   0.03      4.474576271186441                     60\n               19.99999      1.892167321063162                   0.03      4.401815124031417                     60\n              29.999985      1.981169370951423                   0.03      4.449866952489764                     60\n      39.99998000000001      1.946924623152874                   0.03       4.28082762798587                     60\n      49.99997500000001      1.877503805438475                   0.03      4.313413858338581                     60\n               59.99997      1.923558373200694                   0.03      4.122375910919738                     60\n              69.999965      1.991374276760186                   0.03      4.288056283667114                     60\n      79.99996000000002      2.034852953308714                   0.03      4.401864492067443                     60\n      89.99995500000001      2.009007811426452                   0.03      4.178645517121367                     60\n      99.99995000000001      2.040747121218932                   0.03      4.227662187863662                     60\n             109.999945      2.105794671640882                   0.03      4.454419192035694                     60\n              119.99994      2.118230057208461                   0.03       4.34660010778251                     60\n             129.999935       2.19161182147467                   0.03      4.466269795579052                     60\n              139.99993      2.168699559959583                   0.03      4.330357874890133                     60\n             149.999925      2.179664813552677                   0.03      4.214318279473599                     60\n              159.99992      2.225517018370366                   0.03      4.344881648055366                     60\n             169.999915      2.252956281563212                   0.03      4.365101731927973                     60\n              179.99991      2.158216467516354                   0.03      4.104224326478797                     60\n             189.999905      2.137702904676094                   0.03      4.062578778260011                     60\n               199.9999       2.12786266512857                   0.03      3.990064941948607                     60\n             209.999895      2.072031465019663                   0.03      4.186149852737829                     60\n              219.99989       2.03897790015083                   0.03      4.021684326186185                     60\n             229.999885      2.043386841255727                   0.03      3.924945601265422                     60\n              239.99988      2.102659530840184                   0.03      3.946074428954507                     60\n             249.999875      2.055064552068908                   0.03      3.837711697722861                     60\n              259.99987      2.064304654049816                   0.03      3.771360017266983                     60\n      269.9998650000001      2.082346638129076                   0.03       3.74172708809058                     60\n              279.99986      2.103140780243868                   0.03      3.698597801033552                     60\n             289.999855      2.086641704932759                   0.03      3.583360515086035                     60\n              299.99985      2.193729768890007                   0.03      3.970903109595664                     60\n      309.9998450000001      2.254014201149308                   0.03      4.228033937181123                     60\n      319.9998400000001      2.296976084099911                   0.03      4.378005817798226                     60\n             329.999835      2.279400908413092                   0.03      4.167274213839869                     60\n              339.99983      2.330737739496357                   0.03       4.36826493634221                     60\n             349.999825      2.383505707744581                   0.03      4.445013244008961                     60\n      359.9998200000001      2.352048542893706                   0.03      4.268891983800078                     60\n      369.9998150000001      2.422388361997158                   0.03      4.408476902794134                     60\n              379.99981      2.377964166651093                   0.03      4.179267793920304                     60\n             389.999805      2.436441221739456                   0.03      4.309966694482626                     60\n      399.9998000000001      2.389997173806131                   0.03       4.05864252691786                     60\n      409.9997950000001      2.325978258333364                   0.03      4.079907759339392                     60\n              419.99979      2.348902200545417                   0.03      3.938974912591778                     60\n             429.999785      2.274904092551954                   0.03      3.978264351067843                     60\n              439.99978      2.291675706413703                   0.03      3.884454418093366                     60\n      449.9997750000001       2.30300297003753                   0.03      3.796696656875697                     60\n      459.9997700000001      2.235282275783848                   0.03      3.906561205350792                     60\n             469.999765      2.216047367801826                   0.03      3.836732601108184                     60\n              479.99976      2.296071040728819                   0.03      3.680644635908406                     60\n      489.9997550000001      2.337988111561342                   0.03      3.731429934290804                     60\n      499.9997500000001      2.353072835204372                   0.03      3.694673667593633                     60\n      509.9997450000001      2.239254031705672                   0.03      3.705620541860418                     60\n      519.9997400000001      2.201294680626651                   0.03      3.695151595183221                     60\n      529.9997350000001      2.223023239094139                   0.03      3.583627339269668                     60\n      539.9997300000001      2.289186511647509                   0.03      3.522288205953354                     60\n             549.999725      2.281417870653616                   0.03      3.442285355678383                     60\n              559.99972       2.30774291321352                   0.03      3.405571970627217                     60\n             569.999715      2.254950313428867                   0.03      3.400285708862157                     60\n      579.9997100000001      2.180796256949381                   0.03      3.611733760399261                     60\n      589.9997050000001       2.17352780906578                   0.03      3.557503137715996                     60\n      599.9997000000001      2.185015971235476                   0.03      3.430187521909543                     60\n      609.9996950000001      2.177149838063956                   0.03      3.381811317132324                     60\n      619.9996900000001      2.135637417868443                   0.03      3.542209725183163                     60\n      629.9996850000001      2.150164703766263                   0.03      3.406024256144131                     60\n      639.9996800000001      2.129375893087284                   0.03      3.407840443987344                     60\n             649.999675      2.109291630577637                   0.03      3.380624461540454                     60\n              659.99967      2.107667982722176                   0.03      3.308734975273957                     60\n             669.999665       2.06464618672774                   0.03       3.43006517244279                     60\n      679.9996600000001      2.021653395045278                   0.03      3.678899729290001                     60\n      689.9996550000001      1.971946509935128                   0.03      3.973670366174037                     60\n      699.9996500000001      1.973837280725035                   0.03      3.861873050797447                     60\n      709.9996450000001      1.942880250536413                   0.03      3.879947489795478                     60\n      719.9996400000001      2.007994681604727                   0.03      3.612512794394871                     60\n      729.9996350000001      1.966460192282625                   0.03      3.684296783476312                     60\n      739.9996300000001       1.91953747328944                   0.03      3.853598724311625                     60\n             749.999625      1.967824525125812                   0.03      3.564354121846671                     60\n              759.99962      2.001559284176911                   0.03      3.464466925002611                     60\n      769.9996150000001       1.98523996447059                   0.03      3.398050863501483                     60\n      779.9996100000001       2.02371392268137                   0.03      3.328003217159825                     60\n      789.9996050000001       2.00947752158513                   0.03      3.257479831740532                     60\n      799.9996000000001      1.919356833325581                   0.03      3.721837061847233                     60\n      809.9995950000001      1.879090160446324                   0.03      4.046259450758672                     60\n      819.9995900000001      1.848083706553037                   0.03      4.259944830357724                     60\n      829.9995850000001      1.790009745771823                   0.03      4.452157662674875                     60\n              839.99958      1.801035584189908                   0.03      4.305544267802351                     60\n             849.999575      1.826691661962931                   0.03      4.162164521845004                     60\n      859.9995700000001      1.779084068927238                   0.03      4.213186839322378                     60\n      869.9995650000001      1.795746830676238                   0.03      4.024039155966973                     60\n      879.9995600000001      1.860592527808574                   0.03      3.934848900484901                     60\n      889.9995550000001      1.801872283174859                   0.03      3.893254283728352                     60\n      899.9995500000001      1.852413695768293                   0.03      3.835610302114098                     60\n      909.9995450000001      1.843450045848376                   0.03      3.750763545337112                     60\n      919.9995400000001      1.880377702298139                   0.03          3.64491921176                     60\n      929.9995350000002      1.840990682344494                   0.03      3.622522579448166                     60\n              939.99953       1.73138976613732                   0.03      4.391836689959697                     60\n      949.9995250000001      1.722976373156725                   0.03      4.304296338102657                     60\n      959.9995200000001      1.764166582993448                   0.03      3.969432473492251                     60\n      969.9995150000001      1.723785686059089                   0.03      4.133245203292758                     60\n      979.9995100000001      1.734784764170581                   0.03      3.961611253024349                     60\n      989.9995050000001      1.693590249483449                   0.03      4.211832970686954                     60\n      999.9995000000001      1.704915681074797                   0.03      3.986564377918819                     60\n            1009.999495      1.646175387392635                   0.03      4.409247686997852                     60\n             1019.99949      1.662385314298749                   0.03      4.203688656616285                     60\n            1029.999485      1.695051609249376                   0.03      3.885434880549205                     60\n             1039.99948       1.66605097902569                   0.03      4.000150659674903                     60\n            1049.999475      1.639482781886945                   0.03      4.121494323065433                     60\n             1059.99947      1.619111104743821                   0.03       4.20455468266236                     60\n            1069.999465      1.680594451128464                   0.03       3.74292714056601                     60\n             1079.99946      1.618769725426063                   0.03      4.078314784168332                     60\n            1089.999455      1.592360371059557                   0.03       4.23538386444253                     60\n             1099.99945      1.578571621361703                   0.03      4.236209868828013                     60\n            1109.999445      1.531824852899437                   0.03      4.417613313775123                     60\n             1119.99944      1.550091503758405                   0.03      4.223975806372501                     60\n            1129.999435      1.522944956134368                   0.03      4.237302666700748                     60\n             1139.99943      1.586754662521754                   0.03      3.966087388401239                     60\n            1149.999425      1.590529762051784                   0.03       3.85068953254191                     60\n             1159.99942      1.625426485869542                   0.03      3.715711139606795                     60\n            1169.999415       1.65571064321342                   0.03      3.629088292132512                     60\n             1179.99941      1.708621240572108                   0.03      3.591880101203485                     60\n            1189.999405      1.742651747108936                   0.03      3.659593805753154                     60\n              1199.9994      1.763989485880559                   0.03      3.643544000759827                     60\n            1209.999395      1.781425924422409                   0.03      3.568715357713961                     60\n             1219.99939      1.811423876896886                   0.03      3.521308884528906                     60\n            1229.999385      1.821029362538498                   0.03      3.451474436655267                     60\n             1239.99938      1.864817856381295                   0.03      3.457741173615077                     60\n            1249.999375      1.844431914252507                   0.03      3.346298525085595                     60\n             1259.99937      1.761461808147131                   0.03      3.450612215775936                     60\n            1269.999365      1.765971254709585                   0.03      3.362653767683264                     60\n             1279.99936      1.768860406898948                   0.03      3.281865638244601                     60\n            1289.999355      1.817852448325947                   0.03      3.247320828837732                     60\n             1299.99935      1.829836495076306                   0.03      3.191255101249151                     60\n            1309.999345      1.768590422220136                   0.03      3.184243484538844                     60\n             1319.99934      1.743892139421473                   0.03      3.229131412363768                     60\n            1329.999335      1.812857505536043                   0.03      3.087295415170739                     60\n             1339.99933      1.812442218604254                   0.03      3.023255359414607                     60\n            1349.999325      1.925401927407047                   0.03      3.489938526542016                     60\n             1359.99932       1.87851383794047                   0.03      3.321353551830593                     60\n            1369.999315      1.927196013655989                   0.03      3.385100124289698                     60\n             1379.99931      1.875717934868814                   0.03      3.213069721950827                     60\n            1389.999305      1.897766802555249                   0.03      3.250123827656247                     60\n              1399.9993      1.915074574722235                   0.03         3.227419914339                     60\n            1409.999295       1.86570344548251                   0.03      3.036186937992841                     60\n             1419.99929      1.815655702067577                   0.03      2.935291365544703                     60\n            1429.999285      1.712969700418707                   0.03      3.331837365978224                     60\n             1439.99928      1.730835934937825                   0.03      3.165978356494481                     60\n            1449.999275       1.67725998304114                   0.03      3.432917807567421                     60\n             1459.99927      1.667846028040365                   0.03      3.396415879416745                     60\n            1469.999265      1.606156451201699                   0.03      3.611993774654721                     60\n             1479.99926      1.568467584007312                   0.03      3.783022218811743                     60\n            1489.999255       1.66449903904962                   0.03       3.32121973133459                     60\n             1499.99925      1.706892289375583                   0.03      3.139254711410028                     60\n            1509.999245      1.693308338412182                   0.03      3.114078067085889                     60\n             1519.99924      1.763380279128213                   0.03      2.967839214942714                     60\n            1529.999235      1.715453840414583                   0.03      2.987782175800653                     60\n             1539.99923      1.765665307756026                   0.03      2.890832386967794                     60\n            1549.999225       1.89310406573135                   0.03      3.067336808120572                     60\n             1559.99922      1.842276257127819                   0.03      2.881456473391236                     60\n            1569.999215      1.802822172217459                   0.03      2.812189421113605                     60\n             1579.99921      1.699849644722038                   0.03      2.966914409076652                     60\n            1589.999205       1.73675216102333                   0.03      2.841766935461727                     60\n              1599.9992      1.686039660597145                   0.03      2.966035236992358                     60\n            1609.999195      1.620838172257308                   0.03      3.408087899649557                     60\n             1619.99919       1.56947868236725                   0.03      3.660604842164555                     60\n            1629.999185      1.548050063970544                   0.03      3.774357567023247                     60\n             1639.99918      1.554301083771055                   0.03      3.620842452131457                     60\n            1649.999175      1.516667123773491                   0.03      3.994187328384302                     60\n             1659.99917      1.491812148620772                   0.03      4.207513662872083                     60\n            1669.999165      1.470027943289499                   0.03      4.293469888643003                     60\n             1679.99916      1.425983976225337                   0.03      4.418462826564361                     60\n            1689.999155      1.456138987019658                   0.03      4.192274061443779                     60\n             1699.99915      1.502278661148016                   0.03      3.871897935095499                     60\n            1709.999145       1.44147633922695                   0.03      4.124034170253206                     60\n             1719.99914      1.419203194875647                   0.03      4.163257627724734                     60\n            1729.999135      1.383561088751079                   0.03       4.33879283106946                     60\n             1739.99913      1.369013162184993                   0.03       4.30120896419434                     60\n            1749.999125      1.347112323008523                   0.03      4.305107551905023                     60\n             1759.99912      1.281998454836512                   0.03      4.460679832141914                     60\n            1769.999115      1.328691775935051                   0.03      4.254923565810897                     60\n             1779.99911      1.307112272269052                   0.03      4.215893697960607                     60\n            1789.999105      1.333316904598344                   0.03      4.038456643683416                     60\n              1799.9991      1.387213431339825                   0.03      4.001222359037418                     60\n            1809.999095      1.334290389121791                   0.03      3.906961494253138                     60\n             1819.99909      1.423266725673705                   0.03      3.890260713105749                     60\n            1829.999085      1.460151227885393                   0.03      3.830363385788915                     60\n             1839.99908      1.440672554806633                   0.03      3.719516335605705                     60\n            1849.999075      1.492059244641194                   0.03       3.72369838936337                     60\n             1859.99907      1.470786374627965                   0.03      3.620163979749126                     60\n            1869.999065      1.460108075704858                   0.03      3.524945000035808                     60\n             1879.99906       1.38038293395342                   0.03      3.804894650596628                     60\n            1889.999055      1.423737013099159                   0.03      3.558643746167922                     60\n             1899.99905      1.445877906240224                   0.03      3.395041108777327                     60\n            1909.999045      1.373164496437037                   0.03      3.688210589924609                     60\n             1919.99904      1.373543915995334                   0.03      3.597051331937763                     60\n            1929.999035       1.29568139148558                   0.03      4.034945302841225                     60\n             1939.99903      1.283012453390585                   0.03      4.045301519574118                     60\n            1949.999025      1.272765927077999                   0.03      4.039145609768964                     60\n             1959.99902      1.225067863789068                   0.03      4.390334922403022                     60\n            1969.999015      1.221102713372281                   0.03      4.282132338253202                     60\n             1979.99901       1.24801554284745                   0.03      4.035176134352331                     60\n            1989.999005      1.205963322695494                   0.03      4.196244559330026                     60\n               1999.999      1.201853144822506                   0.03      4.110959220567033                     60\n            2009.998995      1.147335155248532                   0.03       4.42224956236652                     60\n             2019.99899      1.167529437619733                   0.03      4.207306242946581                     60\n            2029.998985       1.15732396065077                   0.03      4.143029218940363                     60\n             2039.99898      1.107682140925555                   0.03      4.370736930682515                     60\n            2049.998975      1.206849691381731                   0.03      3.872373555328134                     60\n             2059.99897       1.22121846101125                   0.03      3.769661231320821                     60\n            2069.998965      1.250960233264041                   0.03      3.752888013778791                     60\n             2079.99896      1.306737318260266                   0.03      3.668402969998513                     60\n            2089.998955      1.280577631736011                   0.03      3.620107297754571                     60\n             2099.99895      1.314196730995735                   0.03      3.526941446324429                     60\n            2109.998945      1.231760022254876                   0.03      3.593523511730661                     60\n             2119.99894      1.172773958539536                   0.03      3.857183613510661                     60\n            2129.998935      1.189956552295257                   0.03      3.640131781720882                     60\n             2139.99893      1.160600355540818                   0.03      3.787043686391895                     60\n            2149.998925      1.145784155838789                   0.03       3.83709842323784                     60\n             2159.99892      1.107704743630363                   0.03      4.160540784508434                     60\n            2169.998915      1.086172712116576                   0.03      4.233695459445162                     60\n             2179.99891      1.103999212570072                   0.03      3.983528986364367                     60\n            2189.998905      1.052112215998914                   0.03      4.336257047540284                     60\n              2199.9989      1.065809209188046                   0.03      4.113634824337502                     60\n            2209.998895      1.111088251822121                   0.03       3.78352654435392                     60\n             2219.99889      1.030120418847745                   0.03      4.279397010447496                     60\n            2229.998885      1.056227652771565                   0.03      3.976375997466946                     60\n             2239.99888      1.046318112367422                   0.03      3.942234922261734                     60\n            2249.998875     0.9794718760200809                   0.03       4.42163927715731                     60\n             2259.99887     0.9497015574622026                   0.03      4.390270781855375                     60\n            2269.998865      1.001459565788099                   0.03      4.166203312859914                     60\n             2279.99886      1.018748718457388                   0.03      3.961074985007668                     60\n            2289.998855     0.9547806664277502                   0.03      4.202161073754376                     60\n             2299.99885     0.9710077184959686                   0.03      4.022335336705306                     60\n            2309.998845     0.9712609001456495                   0.03      3.914224933944503                     60\n             2319.99884     0.9267324668435276                   0.03      4.189805256118009                     60\n            2329.998835     0.9256751751871946                   0.03      4.084253997027987                     60\n             2339.99883     0.9498719110423832                   0.03      3.786286530669332                     60\n            2349.998825     0.8862622777256253                   0.03      4.334900511853476                     60\n             2359.99882     0.8885928847568877                   0.03      4.193246040154556                     60\n            2369.998815     0.8848664365528063                   0.03      4.103773286713648                     60\n             2379.99881     0.8315117382592693                   0.03      4.403776943520631                     60\n            2389.998805      0.876076627820973                   0.03      4.020459157762054                     60\n              2399.9988     0.8640498401538138                   0.03       3.99702609492648                     60\n            2409.998795     0.8350809991457024                   0.03      4.144219890184446                     60\n             2419.99879     0.8503982135699285                   0.03      3.909382281229895                     60\n            2429.998785     0.8944981874022586                   0.03      3.721523602979718                     60\n             2439.99878     0.9014313830319941                   0.03      3.642042172685707                     60\n            2449.998775     0.9434556932398162                   0.03      3.608539930481561                     60\n             2459.99877     0.9979660682557707                   0.03      3.746883819409099                     60\n            2469.998765      1.000164178944219                   0.03      3.661819862887549                     60\n             2479.99876       1.08366491103746                   0.03       3.67608173321495                     60\n            2489.998755      1.062238060304773                   0.03      3.606390979793496                     60\n             2499.99875      1.076435237491057                   0.03      3.513841538809297                     60\n            2509.998745      1.120528606420947                   0.03      3.563526824857013                     60\n             2519.99874      1.136034595312483                   0.03       3.50804704333081                     60\n            2529.998735       1.20664035322298                   0.03      3.424787689675386                     60\n             2539.99873      1.261526045720567                   0.03       3.48344255686481                     60\n            2549.998725      1.317196072936721                   0.03      3.432047330486065                     60\n      2559.998720000001      1.355193060020091                   0.03      3.452976026903547                     60\n            2569.998715      1.385661826850632                   0.03      3.429932990340639                     60\n             2579.99871      1.355721382022345                   0.03      3.327660041180717                     60\n            2589.998705      1.369821338514036                   0.03      3.266821704143306                     60\n              2599.9987      1.432839181424402                   0.03      3.302166594759921                     60\n            2609.998695      1.403388628853168                   0.03      3.260787887376396                     60\n             2619.99869      1.408909970571676                   0.03      3.193163468663938                     60\n            2629.998685      1.412457040892072                   0.03      3.126102179391276                     60\n             2639.99868      1.440999859664301                   0.03      3.113172450852175                     60\n            2649.998675      1.408891363138839                   0.03      3.024841778173081                     60\n             2659.99867      1.362083866715702                   0.03      3.100773313279267                     60\n            2669.998665      1.391052743961068                   0.03      2.959859337123283                     60\n             2679.99866      1.335325128731259                   0.03      3.157488864631136                     60\n            2689.998655      1.286142499713371                   0.03       3.31610645001978                     60\n             2699.99865      1.242141275200282                   0.03      3.347731758440975                     60\n            2709.998645      1.238661890367861                   0.03      3.270725786976181                     60\n             2719.99864      1.232985408958557                   0.03      3.197120656929177                     60\n            2729.998635      1.279507296329621                   0.03      3.186884470518445                     60\n      2739.998630000001      1.246265108953291                   0.03      3.108309079214591                     60\n            2749.998625       1.24392198886552                   0.03      3.043104544136989                     60\n             2759.99862      1.178347183125411                   0.03      3.352349938140835                     60\n            2769.998615      1.152722557814546                   0.03      3.367038055878372                     60\n             2779.99861        1.1391786216011                   0.03      3.321195977348192                     60\n            2789.998605      1.131240415300223                   0.03      3.265368666155736                     60\n              2799.9986      1.164960488152529                   0.03       3.17682878482329                     60\n            2809.998595      1.099157850305842                   0.03      3.288348326618264                     60\n             2819.99859      1.074653527382181                   0.03      3.320365166276567                     60\n            2829.998585      1.019928244599364                   0.03      3.557462424298449                     60\n             2839.99858       1.12176540381889                   0.03       3.12275092413585                     60\n      2849.998575000001      1.140519136026723                   0.03      3.043893671087502                     60\n             2859.99857       1.18840821858253                   0.03      3.083015890702806                     60\n            2869.998565       1.18538586928706                   0.03      3.019527057283007                     60\n             2879.99856      1.145723923297682                   0.03      2.938843570041636                     60\n            2889.998555      1.120201086355545                   0.03      2.959899573482294                     60\n             2899.99855      1.195656056566947                   0.03      2.940267016591745                     60\n            2909.998545      1.132899151461022                   0.03      2.849637658756689                     60\n      2919.998540000001      1.099653643523241                   0.03      2.987571796092057                     60\n            2929.998535      1.043199786122259                   0.03      3.371122727184687                     60\n             2939.99853      1.042262789549945                   0.03      3.301248983878005                     60\n            2949.998525      1.062186682331999                   0.03      3.116990470213883                     60\n      2959.998520000001      1.003639935519775                   0.03      3.410497453986102                     60\n            2969.998515      0.997811257421258                   0.03      3.351212055584713                     60\n             2979.99851     0.9879126501926562                   0.03      3.304390331966109                     60\n            2989.998505      0.921936131903633                   0.03      3.511252974061818                     60\n              2999.9985      0.943214938417633                   0.03      3.375030537563926                     60\n            3009.998495     0.9310365444231804                   0.03      3.340128566263829                     60\n             3019.99849     0.8486660274473425                   0.03      3.764336177899402                     60\n      3029.998485000001     0.7953332006955038                   0.03      4.302702882220341                     60\n             3039.99848     0.8407716495169326                   0.03      3.723284820205021                     60\n            3049.998475     0.7862458441097246                   0.03      4.230852092582865                     60\n             3059.99847     0.7625386152741439                   0.03      4.291777432656453                     60\n            3069.998465     0.7569503964422213                   0.03      4.206689161981244                     60\n             3079.99846     0.8035712932763892                   0.03      3.885260495000109                     60\n            3089.998455     0.7622563287537538                   0.03      4.016154758910908                     60\n      3099.998450000001     0.8060265488654055                   0.03      3.737495973795209                     60\n            3109.998445     0.7773815352237176                   0.03      3.764134654723999                     60\n             3119.99844     0.7380314194497752                   0.03      4.085559478900989                     60\n            3129.998435     0.7252715739741417                   0.03       4.13216766238792                     60\n      3139.998430000001     0.6771857653139197                   0.03      4.417561533045197                     60\n            3149.998425     0.6473853080325543                   0.03      4.389228787452319                     60\n             3159.99842     0.6839619580731696                   0.03      4.203855166078731                     60\n            3169.998415     0.7129046372422253                   0.03      4.014323447553182                     60\n             3179.99841     0.7244172567624367                   0.03      3.847409567137875                     60\n            3189.998405     0.7011914112967194                   0.03       3.88195326715962                     60\n              3199.9984     0.6514359906174537                   0.03       4.13768066854659                     60\n      3209.998395000001     0.6093835837346429                   0.03      4.354101653422948                     60\n             3219.99839     0.6528126171396791                   0.03      3.972887633247868                     60\n            3229.998385     0.6396972180865274                   0.03      3.950158109141365                     60\n             3239.99838     0.6122671406143186                   0.03      4.094735299674997                     60\n      3249.998375000001     0.5705572507643593                   0.03       4.35442362000255                     60\n             3259.99837     0.5484133171275745                   0.03      4.346322726352708                     60\n            3269.998365     0.5583853716752116                   0.03      4.179650989201667                     60\n      3279.998360000001     0.6123088317690463                   0.03      3.905754441198467                     60\n            3289.998355     0.5677998828053413                   0.03      4.000891692930902                     60\n             3299.99835     0.6174596295776681                   0.03      3.753415523287687                     60\n            3309.998345      0.667646476235629                   0.03      3.682107057217581                     60\n      3319.998340000001     0.5149540414311858                   0.03      4.313258057742529                     60\n            3329.998335     0.5546612672762969                   0.03      3.905811583358553                     60\n             3339.99833      0.602151694164478                   0.03      3.682544474582694                     60\n            3349.998325     0.6974772297593481                   0.03      3.659349393825349                     60\n             3359.99832     0.7395159953965427                   0.03      3.589672030594547                     60\n            3369.998315     0.7396168221795548                   0.03      3.503994856717489                     60\n             3379.99831     0.7690865325222039                   0.03      3.468002171232443                     60\n      3389.998305000001     0.8208527775510952                   0.03      3.535580514517195                     60\n              3399.9983     0.7875786717056461                   0.03      3.413882808976238                     60\n            3409.998295     0.8521249941336673                   0.03      3.411661376528685                     60\n             3419.99829     0.8736521678602089                   0.03      3.329302711929464                     60\n      3429.998285000001     0.9081967730904805                   0.03      3.279990678033851                     60\n             3439.99828     0.8885069503926941                   0.03       3.20950695528191                     60\n            3449.998275     0.8573434466268549                   0.03      3.209565969054643                     60\n      3459.998270000001     0.8236257172679515                   0.03      3.298799024907888                     60\n            3469.998265     0.8188884394396359                   0.03      3.242435289711083                     60\n             3479.99826     0.8173789788622015                   0.03      3.177082573499408                     60\n            3489.998255       0.85369644590983                   0.03      3.048235283416524                     60\n      3499.998250000001     0.9265506852078775                   0.03      3.160818617780278                     60\n            3509.998245     0.9627703734003904                   0.03      3.152814644681042                     60\n             3519.99824     0.9635762556443335                   0.03      3.087959240388606                     60\n            3529.998235     0.9360198189158186                   0.03      3.021683426331461                     60\n      3539.998230000001      1.011696145942459                   0.03      3.137492659859205                     60\n            3549.998225      1.030846189863509                   0.03      3.078659000995008                     60\n             3559.99822      1.016647172159343                   0.03       3.02084180844276                     60\n      3569.998215000001      1.035777307228268                   0.03      2.962198034570752                     60\n             3579.99821      1.038098405028382                   0.03      2.904379755830394                     60\n            3589.998205      1.043903133837678                   0.03      2.852099348932159                     60\n              3599.9982     0.9876986329098038                   0.03      2.924256482440294                     60\n      3609.998195000001     0.9834229494208372                   0.03      2.875642316675664                     60\n             3619.99819     0.9941311229055534                   0.03      2.801578813675352                     60\n            3629.998185     0.9262389259143875                   0.03      2.953852265375147                     60\n      3639.998180000001      0.910481709536491                   0.03      2.944299696845065                     60\n      3649.998175000001     0.9037671841473536                   0.03      2.902809400664719                     60\n             3659.99817     0.9474768906192799                   0.03      2.788068356048298                     60\n            3669.998165     0.8704090219518651                   0.03      2.917602149733083                     60\n      3679.998160000001     0.9039061904797895                   0.03      2.798350760518074                     60\n            3689.998155     0.9245583001041745                   0.03      2.716707674263237                     60\n             3699.99815     0.9660448578923272                   0.03      2.710295027718987                     60\n            3709.998145     0.9314070018793971                   0.03      2.640262989110285                     60\n      3719.998140000001     0.9894325525963831                   0.03      2.681322352548585                     60\n            3729.998135      1.002557284299812                   0.03      2.653328956718157                     60\n             3739.99813      1.014450585595467                   0.03       2.63199755928893                     60\n      3749.998125000001      1.057951548560542                   0.03      2.782904086301909                     60\n             3759.99812      1.088893910420536                   0.03      2.834858389345875                     60\n            3769.998115      1.024036897250584                   0.03      2.585895274401956                     60\n             3779.99811      1.084100309058272                   0.03      2.770475210441392                     60\n      3789.998105000001       1.11263498530422                   0.03      2.728015471827893                     60\n              3799.9981      1.126338714706578                   0.03      2.679088437792165                     60\n            3809.998095      1.163678536781044                   0.03      2.763674785219473                     60\n      3819.998090000001       1.17781977031251                   0.03      2.781142652745638                     60\n      3829.998085000001      1.225435825193506                   0.03      2.873352033533432                     60\n             3839.99808      1.204928372264197                   0.03      2.781047948576533                     60\n            3849.998075      1.162545591105284                   0.03      2.639256751177953                     60\n      3859.998070000001      1.156331807732533                   0.03      2.577552984826066                     60\n            3869.998065      1.074559424725522                   0.03      2.663103197678147                     60\n             3879.99806      1.081031236937508                   0.03      2.619360678015932                     60\n            3889.998055      1.135719637252026                   0.03      2.512966338003618                     60\n      3899.998050000001      1.212914505264659                   0.03      2.721965583735063                     60\n            3909.998045      1.280217990538272                   0.03      3.035207969508979                     60\n             3919.99804      1.260447397205907                   0.03      2.888957562797152                     60\n      3929.998035000001      1.279025321276609                   0.03      2.922177770793724                     60\n      3939.998030000001      1.349361010049621                   0.03      2.996862865708738                     60\n            3949.998025      1.301683742208174                   0.03      2.958086851495134                     60\n             3959.99802      1.344825623940494                   0.03      2.931903793462441                     60\n      3969.998015000001      1.327733521360438                   0.03      2.905923138576929                     60\n             3979.99801       1.39907449745362                   0.03      2.860079152938859                     60\n            3989.998005       1.46590234233916                   0.03      3.209049708241428                     60\n      3999.998000000001      1.470021458846221                   0.03      3.183676725472094                     60\n      4009.997995000001      1.496326284911016                   0.03      3.383757577018785                     60\n             4019.99799      1.450431849765822                   0.03      2.924184805184256                     60\n            4029.997985      1.527680390364895                   0.03      3.459422291929261                     60\n      4039.997980000001      1.521130057796296                   0.03      3.367534304292285                     60\n            4049.997975      1.517723426778061                   0.03      3.283419243333698                     60\n             4059.99797      1.489405597497467                   0.03      3.102288337798899                     60\n            4069.997965      1.509467104602743                   0.03      3.135146266403461                     60\n      4079.997960000001      1.507435396394205                   0.03      3.061287974613662                     60\n            4089.997955      1.529782723544811                   0.03      3.113415545908333                     60\n      4099.997950000001      1.567723461443914                   0.03      3.269893002940424                     60\n            4109.997945      1.573850533243203                   0.03      3.220261364273591                     60\n             4119.99794      1.519196414881094                   0.03      2.963995438536945                     60\n            4129.997935      1.484492907382715                   0.03      2.870010418438777                     60\n             4139.99793      1.470117775261845                   0.03      2.800140206351108                     60\n      4149.997925000001      1.500676654015778                   0.03      2.799678308716564                     60\n      4159.997920000001       1.60832478635351                   0.03        3.2534846251136                     60\n      4169.997915000001      1.577296812465389                   0.03      3.110176004522836                     60\n             4179.99791      1.564582274871174                   0.03      3.012667350634181                     60\n            4189.997905      1.559647718866769                   0.03      2.938833221972023                     60\n              4199.9979       1.60756646291459                   0.03      3.102173350259798                     60\n            4209.997895      1.598223097110361                   0.03      2.990365828198444                     60\n      4219.997890000001      1.636425420891984                   0.03      3.101591570167895                     60\n      4229.997885000001      1.633048188400101                   0.03      3.032236167863115                     60\n      4239.997880000001      1.559330372596913                   0.03      2.834599185751023                     60\n            4249.997875      1.594963866038726                   0.03      2.839134135684459                     60\n             4259.99787      1.613013826031131                   0.03      2.859839582281993                     60\n            4269.997865      1.623175505621617                   0.03      2.853663830399583                     60\n             4279.99786      1.615387058859972                   0.03      2.764532791936702                     60\n      4289.997855000001      1.554021600469081                   0.03      2.741468528902707                     60\n      4299.997850000001      1.556886870432891                   0.03      2.685941538564122                     60\n      4309.997845000001      1.543217143491639                   0.03      2.664507108621315                     60\n      4319.997840000001      1.540816642863258                   0.03       2.62154555311913                     60\n            4329.997835      1.625761246829369                   0.03      2.754752621462036                     60\n             4339.99783      1.665600891409936                   0.03      2.879105898568334                     60\n            4349.997825      1.690993696913076                   0.03       2.79770493321987                     60\n      4359.997820000001      1.722232496319438                   0.03      2.737922330698658                     60\n      4369.997815000001      1.678666922318353                   0.03      2.751722578957338                     60\n      4379.997810000001      1.667405231272246                   0.03      2.728756308895832                     60\n      4389.997805000001      1.639617377717524                   0.03      2.683496446591252                     60\n              4399.9978       1.63060957490946                   0.03      2.616991793196869                     60\n            4409.997795      1.641816015093477                   0.03      2.596319714500287                     60\n             4419.99779      1.723235891926831                   0.03      2.661805987109513                     60\n            4429.997785      1.722274614135334                   0.03      2.612021288184976                     60\n      4439.997780000001      1.680244132932114                   0.03      2.567968715251731                     60\n      4449.997775000001      1.679890106190101                   0.03      2.524418751866584                     60\n      4459.997770000001      1.730347949867757                   0.03      2.569482533936005                     60\n            4469.997765      1.791985006019065                   0.03      2.739732068640155                     60\n             4479.99776      1.744520860636586                   0.03      2.582183765999635                     60\n            4489.997755      1.783930955550368                   0.03      2.662789529198264                     60\n             4499.99775      1.810672164298743                   0.03      2.677188219999419                     60\n      4509.997745000001      1.814281715673876                   0.03      2.640743631978152                     60\n      4519.997740000001      1.896728034306737                   0.03      3.005194509481763                     60\n      4529.997735000001      1.912955666255264                   0.03      3.026430031044283                     60\n      4539.997730000001      1.922730894177726                   0.03      3.020512915211936                     60\n            4549.997725      1.948426631756301                   0.03      3.121263902884133                     60\n             4559.99772      1.950184683086902                   0.03      3.065505277248814                     60\n            4569.997715       1.96779709203957                   0.03      3.079783002163047                     60\n      4579.997710000001      1.964430347821773                   0.03      3.004699082603371                     60\n      4589.997705000001      2.030908287883167                   0.03      3.184483329361396                     60\n      4599.997700000001      2.007564750989702                   0.03      3.063637429736473                     60\n      4609.997695000001      2.053808675699157                   0.03      3.168527914113798                     60\n             4619.99769      2.083688354469914                   0.03      3.186703935689801                     60\n            4629.997685      2.043775778179129                   0.03       3.03505524704766                     60\n             4639.99768      2.026632548472632                   0.03      2.949356235084576                     60\n      4649.997675000001      1.966108788076231                   0.03       2.91117037168585                     60\n      4659.997670000001      2.000261501847251                   0.03      2.882105357902213                     60\n      4669.997665000001      2.077266863157998                   0.03      3.061542537630599                     60\n      4679.997660000001      2.114824225950679                   0.03      3.119368909182091                     60\n            4689.997655      2.142854751582477                   0.03      3.155034924855644                     60\n             4699.99765      2.176546014132758                   0.03      3.150743830398244                     60\n            4709.997645      2.118794732482482                   0.03      3.011955269490747                     60\n      4719.997640000001      2.093030671872296                   0.03      2.941956740950713                     60\n      4729.997635000001       2.06590776728262                   0.03      2.886951448501792                     60\n      4739.997630000001      2.097331398720122                   0.03      2.851026489381495                     60\n      4749.997625000001      2.161212081844092                   0.03      3.033355647411684                     60\n             4759.99762      2.230490593358516                   0.03      3.310904319823685                     60\n            4769.997615      2.221191236527551                   0.03      3.210743916733771                     60\n             4779.99761      2.230089235036657                   0.03      3.170849879320885                     60\n            4789.997605      2.249824317940336                   0.03      3.158198122670216                     60\n      4799.997600000001        2.2335547766668                   0.03      3.057283883708252                     60\n      4809.997595000001      2.172904777794629                   0.03      2.956067245993391                     60\n      4819.997590000001      2.172127768941236                   0.03      2.897630534708122                     60\n      4829.997585000001       2.32685757008923                   0.03      3.407391271973661                     60\n             4839.99758      2.391007785397345                   0.03      3.826251226453179                     60\n            4849.997575      2.371531621752974                   0.03      3.586080814649403                     60\n             4859.99757      2.458587134531989                   0.03      4.288107589827753                     60\n      4869.997565000001      2.471432767156808                   0.03      4.253887542575054                     60\n      4879.997560000001      2.441145562734314                   0.03      3.979460299766732                     60\n      4889.997555000001      2.441064842822774                   0.03      3.874015408056914                     60\n      4899.997550000001      2.532722252190153                   0.03      4.450835528966484                     60\n            4909.997545      2.547470837461802                   0.03      4.351344340047227                     60\n             4919.99754      2.528851605127759                   0.03      4.209813927520147                     60\n            4929.997535      2.528201894368291                   0.03       4.09255382266422                     60\n      4939.997530000001      2.591495987632848                   0.03      4.384412195694711                     60\n      4949.997525000001       2.59317796755863                   0.03      4.265555914599476                     60\n      4959.997520000001      2.617530101725842                   0.03      4.282909202606398                     60\n      4969.997515000001      2.635080020572662                   0.03      4.274823464900083                     60\n             4979.99751      2.683248665144692                   0.03      4.425948534061602                     60\n            4989.997505      2.693708415784728                   0.03      4.327596129819983                     60\n              4999.9975      2.625730842670156                   0.03      4.070855781449339                     60\n      5009.997495000001      2.661408941724874                   0.03      4.105905308168109                     60\n      5019.997490000001      2.640973463362419                   0.03      3.935977342391598                     60\n      5029.997485000001      2.565763940126232                   0.03      3.972182132779897                     60\n      5039.997480000001      2.523587660457869                   0.03      3.930306604551076                     60\n            5049.997475      2.490701943585749                   0.03      3.978017839311629                     60\n             5059.99747      2.491660376723552                   0.03      3.872166880636302                     60\n            5069.997465      2.544266979337276                   0.03      3.743619823733519                     60\n      5079.997460000001      2.426705251222264                   0.03      3.712355761431894                     60\n      5089.997455000001      2.486579517211727                   0.03      3.748115635827301                     60\n      5099.997450000001      2.477674023747313                   0.03      3.652477972391253                     60\n';

EOF

echo "=== Writing src/App.jsx ==="
cat << 'EOF' > src/App.jsx
import React, { useState } from "react";
import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";
import MetadynamicsLab2D from "./MetadynamicsLab2D";
import HillsVisualizer from "./HillsVisualizer";
import OPESSimulator from "./OPESSimulator";
import OpesVisualizer from "./OpesVisualizer";
import {
  Activity,
  Layers,
  BarChart2,
  ShieldCheck,
  Sliders,
  RefreshCw,
  RotateCcw,
  Zap,
  FileText
} from "lucide-react";

function App() {
  const [simDimension, setSimDimension] = useState("1D"); // "1D" | "2D" | "OPES" | "HILLS" | "OPES_INSPECTOR"

  // Shared state for HILLS visualizer configuration
  const [numBins, setNumBins] = useState(300);
  const [customBiasFactor, setCustomBiasFactor] = useState("");
  const [gridMinUser, setGridMinUser] = useState("");
  const [gridMaxUser, setGridMaxUser] = useState("");
  const [gridMin2User, setGridMin2User] = useState("");
  const [gridMax2User, setGridMax2User] = useState("");

  const [inputNumBins, setInputNumBins] = useState("300");
  const [inputCustomBias, setInputCustomBias] = useState("");
  const [inputGridMin, setInputGridMin] = useState("");
  const [inputGridMax, setInputGridMax] = useState("");
  const [inputGridMin2, setInputGridMin2] = useState("");
  const [inputGridMax2, setInputGridMax2] = useState("");

  const [energyUnits, setEnergyUnits] = useState("kJ/mol");
  const [energyRefMode, setEnergyRefMode] = useState("plateauZero"); // "raw" | "minZero" | "plateauZero"
  const [isWtScaling, setIsWtScaling] = useState(true);

  // Active HILLS metadata detected by visualizer
  const [hillsMetadata, setHillsMetadata] = useState(null);

  const handleApplyGridParams = (e) => {
    if (e) e.preventDefault();
    setNumBins(parseInt(inputNumBins) || 300);
    setCustomBiasFactor(inputCustomBias);
    setGridMinUser(inputGridMin);
    setGridMaxUser(inputGridMax);
    setGridMin2User(inputGridMin2);
    setGridMax2User(inputGridMax2);
  };

  const handleResetGridBounds = () => {
    setInputGridMin("");
    setInputGridMax("");
    setInputGridMin2("");
    setInputGridMax2("");
    setGridMinUser("");
    setGridMaxUser("");
    setGridMin2User("");
    setGridMax2User("");
  };

  return (
    <div className="h-screen max-h-screen bg-slate-950 text-slate-100 p-3 sm:p-4 selection:bg-cyan-500 selection:text-white relative overflow-hidden flex flex-col">
      {/* Background Ambient Glow Effects */}
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Outer Full-Width Responsive Layout */}
      <div className="w-full h-full max-w-[1920px] mx-auto flex flex-col lg:flex-row items-stretch gap-4 min-h-0">
        
        {/* ALWAYS-PRESENT LEFT SIDEBAR */}
        <aside className="w-full lg:w-80 bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-2xl shrink-0 space-y-5">
          
          {/* Brand Logo & Title Header */}
          <div className="flex items-center gap-3 px-1 py-1 border-b border-slate-800/80 pb-3">
            <div className="p-2 bg-gradient-to-br from-cyan-500 to-indigo-600 rounded-xl shadow-lg shadow-cyan-500/20 text-white">
              <Activity size={20} />
            </div>
            <div>
              <h1 className="font-extrabold text-xs text-white tracking-wide">
                METADYNAMICS
              </h1>
              <p className="text-[10px] text-cyan-400 font-mono tracking-wider uppercase font-semibold">
                Laboratory
              </p>
            </div>
          </div>

          {/* Mode Switcher Vertical Button Group */}
          <div className="space-y-4">
            
            {/* Section 1: METADYNAMICS */}
            <div className="space-y-2">
              <div className="px-1 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400 font-mono">
                  Metadynamics
                </span>
              </div>

              <button
                onClick={() => setSimDimension("1D")}
                className={`w-full p-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                  simDimension === "1D"
                    ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 border border-cyan-400/30"
                    : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
                }`}
              >
                <Activity size={17} className={simDimension === "1D" ? "text-white" : "text-cyan-400"} />
                <div>
                  <div>1D Simulator</div>
                  <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">1 Collective Variable</div>
                </div>
              </button>

              <button
                onClick={() => setSimDimension("2D")}
                className={`w-full p-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                  simDimension === "2D"
                    ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/25 border border-purple-400/30"
                    : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
                }`}
              >
                <Layers size={17} className={simDimension === "2D" ? "text-white" : "text-purple-400"} />
                <div>
                  <div>2D Simulator</div>
                  <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">2 Collective Variables</div>
                </div>
              </button>

              <button
                onClick={() => setSimDimension("HILLS")}
                className={`w-full p-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                  simDimension === "HILLS"
                    ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/25 border border-emerald-400/30"
                    : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
                }`}
              >
                <BarChart2 size={17} className={simDimension === "HILLS" ? "text-white" : "text-emerald-400"} />
                <div>
                  <div>HILLS Inspector</div>
                  <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">PLUMED 1D & 2D</div>
                </div>
              </button>
            </div>

            {/* Section 2: OPES METADYNAMICS */}
            <div className="space-y-2 pt-2 border-t border-slate-800/60">
              <div className="px-1 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-400 font-mono">
                  OPES Metadynamics
                </span>
              </div>

              <button
                onClick={() => setSimDimension("OPES")}
                className={`w-full p-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                  simDimension === "OPES"
                    ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/25 border border-amber-400/30"
                    : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
                }`}
              >
                <Zap size={17} className={simDimension === "OPES" ? "text-white" : "text-amber-400"} />
                <div>
                  <div>OPES Simulator</div>
                  <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">On-the-fly Prob. Sampling</div>
                </div>
              </button>

              <button
                onClick={() => setSimDimension("OPES_INSPECTOR")}
                className={`w-full p-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                  simDimension === "OPES_INSPECTOR"
                    ? "bg-gradient-to-r from-amber-600 to-orange-700 text-white shadow-lg shadow-amber-600/25 border border-amber-400/30"
                    : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
                }`}
              >
                <FileText size={17} className={simDimension === "OPES_INSPECTOR" ? "text-white" : "text-amber-400"} />
                <div>
                  <div>OPES Inspector</div>
                  <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">PLUMED OPES_STATE</div>
                </div>
              </button>
            </div>

          </div>

          {/* Footer Info inside left column sidebar */}
          <div className="pt-3 border-t border-slate-800/80 px-1 text-[10px] text-slate-400 leading-relaxed space-y-1.5">
            <div>
              Developed by{" "}
              <a
                href="https://github.com/Alexsg14"
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-slate-200 hover:text-cyan-400 transition-colors underline decoration-slate-700 underline-offset-2"
              >
                Alejandro Seco-Gonzalez
              </a>{" "}
              in collaboration with{" "}
              <span className="font-semibold text-slate-200">Daniel Arias-Ferreiro</span> at{" "}
              <a
                href="https://simbios.usc.es/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-bold text-cyan-400 hover:text-cyan-300 transition-colors underline decoration-cyan-500/40 underline-offset-2"
              >
                SIMBIOS
              </a>
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 text-slate-600"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Files are processed locally — no data is uploaded or stored.
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 w-full min-w-0 h-full overflow-y-auto pr-1">
          {simDimension === "1D" ? (
            <MetadynamicsLab />
          ) : simDimension === "2D" ? (
            <MetadynamicsLab2D />
          ) : simDimension === "OPES" ? (
            <OPESSimulator />
          ) : simDimension === "HILLS" ? (
            <HillsVisualizer
              numBins={numBins}
              customBiasFactor={customBiasFactor}
              gridMinUser={gridMinUser}
              gridMaxUser={gridMaxUser}
              gridMin2User={gridMin2User}
              gridMax2User={gridMax2User}
              setGridMinUser={setGridMinUser}
              setGridMaxUser={setGridMaxUser}
              setGridMin2User={setGridMin2User}
              setGridMax2User={setGridMax2User}
              energyUnits={energyUnits}
              setEnergyUnits={setEnergyUnits}
              energyRefMode={energyRefMode}
              setEnergyRefMode={setEnergyRefMode}
              isWtScaling={isWtScaling}
              setIsWtScaling={setIsWtScaling}
              inputNumBins={inputNumBins}
              setInputNumBins={setInputNumBins}
              inputCustomBias={inputCustomBias}
              setInputCustomBias={setInputCustomBias}
              inputGridMin={inputGridMin}
              setInputGridMin={setInputGridMin}
              inputGridMax={inputGridMax}
              setInputGridMax={setInputGridMax}
              inputGridMin2={inputGridMin2}
              setInputGridMin2={setInputGridMin2}
              inputGridMax2={inputGridMax2}
              setInputGridMax2={setInputGridMax2}
              handleApplyGridParams={handleApplyGridParams}
              handleResetGridBounds={handleResetGridBounds}
              hillsMetadata={hillsMetadata}
              onMetadataLoaded={setHillsMetadata}
            />
          ) : (
            <OpesVisualizer />
          )}
        </main>

      </div>
    </div>
  );
}

export default App;

EOF

echo "=== Writing vite.config.js ==="
cat << 'EOF' > vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})

EOF

