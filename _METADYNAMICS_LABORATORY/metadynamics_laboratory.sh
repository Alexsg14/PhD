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

echo "=== Writing src/MetadynamicsLab.jsx ==="
cat << 'EOF' > src/MetadynamicsLab.jsx
import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Play, Pause, RotateCcw, Activity, TrendingUp, Layers, Plus, Trash2, 
  Crosshair, BookOpen, Thermometer, Save, Upload, Hash, Calculator, 
  Sparkles, Gauge, Zap, Check, HelpCircle, X, Sliders, RefreshCw 
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ReferenceDot, Area, Legend 
} from 'recharts';

function mulberry32(a) {
  return function() {
    var t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function gaussianRandom(rng) {
  let u1 = rng();
  let u2 = rng();
  while (u1 === 0) u1 = rng();
  return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
}

const MATH_PRESETS = [
  { label: 'Symmetric Double Well', expr: '0.5 * (x^2 - 4)^2' },
  { label: 'Asymmetric Double Well', expr: '0.25 * x^4 - 2 * x^2 + 0.8 * x' },
  { label: 'Triple Energy Well', expr: '0.1 * x^6 - 2 * x^4 + 8 * x^2' },
  { label: 'Sinusoidal Wavy Surface', expr: '3 * cos(2 * x) + 0.15 * x^4' },
  { label: 'Harmonic Oscillator', expr: '1.5 * x^2' }
];

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

const getPES = (x, currentWells, pesMode = 'wells', pesFunctionStr = '') => {
  if (pesMode === 'function' && pesFunctionStr.trim()) {
    return parseAndEvalMath(pesFunctionStr, x);
  }
  let energy = 0;
  energy += 0.2 * Math.pow(x, 4);
  currentWells.forEach(well => {
    energy += -well.depth * Math.exp(-Math.pow(x - well.pos, 2) / well.width);
  });
  return energy;
};

const getBias = (x, storedBiases) => {
  let bias = 0;
  for (let g of storedBiases) {
    bias += g.h * Math.exp(-Math.pow(x - g.mu, 2) / (2 * g.sigma * g.sigma));
  }
  return bias;
};

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
  const [isRunning, setIsRunning] = useState(false);
  const [timeStep, setTimeStep] = useState(0);
  const [showGuideModal, setShowGuideModal] = useState(false);
  
  const [pesMode, setPesMode] = useState('wells');
  const [pesFunctionStr, setPesFunctionStr] = useState('0.5 * (x^2 - 4)^2');

  const [wells, setWells] = useState([
    { id: 1, pos: -2, depth: 8, width: 0.8 },
    { id: 2, pos: 2, depth: 8, width: 0.8 }
  ]);

  const [gaussianHeight, setGaussianHeight] = useState(0.5); 
  const [gaussianWidth, setGaussianWidth] = useState(0.4);   
  const [depositionStride, setDepositionStride] = useState(20); 
  const [temperature, setTemperature] = useState(0.8); 

  const [isWellTempered, setIsWellTempered] = useState(false);
  const [biasFactor, setBiasFactor] = useState(10);

  const [walkerPos, setWalkerPos] = useState(-2); 
  const [biasPotentials, setBiasPotentials] = useState([]); 
  const [currentDepositionHeight, setCurrentDepositionHeight] = useState(0.5); 
  
  const [seed, setSeed] = useState(12345);
  const [useFixedSeed, setUseFixedSeed] = useState(false);
  const rngRef = useRef(Math.random);

  const savedCallback = useRef();
  const fileInputRef = useRef(null);

  const initRNG = (currentSeed) => {
    rngRef.current = mulberry32(currentSeed);
  };

  const handleExport = () => {
    const data = {
      version: "2.0",
      pesMode,
      pesFunctionStr,
      wells,
      biasPotentials,
      walkerPos,
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

  const stepSimulation = () => {
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
      return newX;
    });

    setTimeStep((prevTime) => {
      const nextTime = prevTime + 1;
      
      if (nextTime % depositionStride === 0) {
        let newHeight = gaussianHeight;

        if (isWellTempered) {
          const currentBiasV = getBias(walkerPos, biasPotentials);
          const deltaT = temperature * (biasFactor - 1);
          if (deltaT > 0) {
            newHeight = gaussianHeight * Math.exp(-currentBiasV / deltaT);
          }
        }
        
        setCurrentDepositionHeight(newHeight);

        setBiasPotentials(prevBias => [
          ...prevBias,
          { mu: walkerPos, h: newHeight, sigma: gaussianWidth }
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

  const currentPES = getPES(walkerPos, wells, pesMode, pesFunctionStr);
  const currentBiasVal = getBias(walkerPos, biasPotentials);
  const currentForce = getForce(walkerPos, biasPotentials, wells, pesMode, pesFunctionStr);

  return (
    <div className="flex flex-col w-full max-w-7xl mx-auto space-y-6">
      
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 relative overflow-hidden">
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

        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-end z-10">
          
          <div className="hidden sm:flex items-center gap-2 mr-2 bg-slate-950/80 px-3.5 py-1.5 rounded-xl border border-slate-800/80 text-xs">
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Steps</span>
              <span className="font-mono font-bold text-slate-200">{timeStep}</span>
            </div>
            <div className="flex flex-col items-center px-2 border-r border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Hills</span>
              <span className="font-mono font-bold text-cyan-400">{biasPotentials.length}</span>
            </div>
            <div className="flex flex-col items-center px-2">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Height W(t)</span>
              <span className={`font-mono font-bold ${isWellTempered && currentDepositionHeight < 0.05 ? 'text-amber-400' : 'text-slate-200'}`}>
                {currentDepositionHeight.toFixed(3)}
              </span>
            </div>
          </div>

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

          <button
            onClick={() => setShowGuideModal(true)}
            className="py-2 px-3.5 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
          >
            <BookOpen size={16} className="text-cyan-400" />
            <span>Guide</span>
          </button>

          <button
            onClick={handleReset}
            className="p-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 rounded-xl transition-all shadow-sm"
            title="Reset Simulation"
          >
            <RotateCcw size={18} />
          </button>

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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <div className="lg:col-span-4 space-y-5">
          
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="flex justify-between items-center pb-2.5 border-b border-slate-800/80">
              <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                <Crosshair size={16} className="text-cyan-400" />
                Potential Surface (PES)
              </h3>
              
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

          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4.5 shadow-xl space-y-4">
            <div className="pb-2 border-b border-slate-800/80 font-semibold text-xs text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Layers size={16} className="text-cyan-400" />
              Metadynamics Parameters
            </div>
            
            <div className="space-y-4">
              
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

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Initial Hill Height (W₀)</span>
                  <span className="font-mono font-semibold text-cyan-400">{gaussianHeight.toFixed(2)} <span className="text-[10px] text-slate-500">kJ/mol</span></span>
                </div>
                <input type="range" min="0.1" max="2.0" step="0.1" value={gaussianHeight} onChange={(e) => setGaussianHeight(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"/>
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1.5">
                  <span>Gaussian Width (σ)</span>
                  <span className="font-mono font-semibold text-purple-400">{gaussianWidth.toFixed(2)}</span>
                </div>
                <input type="range" min="0.1" max="1.0" step="0.05" value={gaussianWidth} onChange={(e) => setGaussianWidth(parseFloat(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"/>
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
                  <span className="font-mono font-semibold text-emerald-400">{depositionStride} <span className="text-[10px] text-slate-500">steps</span></span>
                </div>
                <input type="range" min="5" max="50" step="5" value={depositionStride} onChange={(e) => setDepositionStride(parseInt(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"/>
              </div>

            </div>
          </div>

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

        <div className="lg:col-span-8 flex flex-col space-y-5">
          
          <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl flex flex-col min-h-[580px] relative">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
                  <TrendingUp size={18} className="text-cyan-400" /> 
                  Real-Time Dynamics & FES Reconstruction
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Overdamped Langevin Diffusion & Accumulated Bias Potential
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                  isWellTempered 
                    ? 'bg-indigo-950/80 text-indigo-300 border-indigo-800/80' 
                    : 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
                }`}>
                  {isWellTempered ? `WT-MetaD (γ = ${biasFactor})` : 'Standard MetaD'}
                </span>
              </div>
            </div>

            <div className="flex-1 w-full min-h-[440px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 25, left: 0, bottom: 25 }}>
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
                    fontSize={11}
                    tickCount={10}
                    label={{ value: 'Collective Variable (CV)', position: 'bottom', offset: 15, fill: '#94a3b8', fontSize: 12 }} 
                  />
                  <YAxis 
                    domain={yDomain} 
                    stroke="#94a3b8" 
                    fontSize={11}
                    label={{ value: 'Energy (kJ/mol)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }} 
                  />
                  <Tooltip content={<CustomGraphTooltip />} />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }}/>
                  
                  <Area 
                    type="monotone" 
                    dataKey="BiasOnly" 
                    stroke="none" 
                    fill="url(#biasGradient)" 
                    isAnimationActive={false} 
                    name="Accumulated Bias V_B(x)" 
                  />

                  <Line 
                    type="monotone" 
                    dataKey="PES" 
                    stroke="#38bdf8" 
                    strokeWidth={3} 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Original PES V(x)" 
                  />

                  <Line 
                    type="monotone" 
                    dataKey="Total" 
                    stroke="#34d399" 
                    strokeWidth={2.5} 
                    strokeDasharray="5 5" 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Total Potential V + V_B" 
                  />
                  
                  <Line 
                    type="monotone" 
                    dataKey="FES_Est" 
                    stroke="#c084fc" 
                    strokeWidth={2.5} 
                    strokeDasharray="8 4" 
                    dot={false} 
                    isAnimationActive={false} 
                    name="Estimated FES F(x)" 
                  />
                  
                  <ReferenceDot 
                    x={walkerPos} 
                    y={currentPES + currentBiasVal} 
                    r={7} 
                    fill="#06b6d4" 
                    stroke="#ffffff" 
                    strokeWidth={2.5} 
                    isAnimationActive={false} 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 shadow-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Walker Pos (x)</span>
              <span className="font-mono text-lg font-bold text-cyan-400">{walkerPos.toFixed(3)}</span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 shadow-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">PES Energy V(x)</span>
              <span className="font-mono text-lg font-bold text-slate-200">{currentPES.toFixed(3)} <span className="text-xs text-slate-500">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 shadow-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Bias Energy V_B(x)</span>
              <span className="font-mono text-lg font-bold text-red-400">{currentBiasVal.toFixed(3)} <span className="text-xs text-slate-500">kJ/mol</span></span>
            </div>
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3.5 shadow-lg">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Net Force (-∇V)</span>
              <span className="font-mono text-lg font-bold text-emerald-400">{currentForce.toFixed(3)}</span>
            </div>
          </div>

        </div>
      </div>

      {showGuideModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto relative">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen size={20} className="text-cyan-400" />
                Metadynamics Simulation Theory Guide
              </h3>
              <button onClick={() => setShowGuideModal(false)} className="text-slate-400 hover:text-white p-1 rounded-lg">
                <X size={20} />
              </button>
            </div>
            
            <div className="text-xs text-slate-300 space-y-3 leading-relaxed">
              <p>
                <strong>Metadynamics</strong> is a powerful enhanced sampling technique in computational physics and chemistry designed to accelerate rare events and reconstruct Free Energy Surfaces (FES) along chosen Collective Variables (CVs).
              </p>
              
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                <h4 className="font-bold text-cyan-400">1. Overdamped Langevin (Brownian) Dynamics</h4>
                <p>
                  The particle position <code className="text-slate-200">x(t)</code> evolves under thermal fluctuations according to:
                </p>
                <div className="font-mono text-[11px] text-slate-300 bg-slate-900 p-2 rounded">
                  dx = -∇ [V(x) + V_B(x, t)] dt + √(2 k_B T dt) · η(t)
                </div>
                <p>where η(t) ~ N(0, 1) is standard Gaussian noise generated via the Box-Muller transform.</p>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                <h4 className="font-bold text-indigo-400">2. Standard vs. Well-Tempered Metadynamics (WT-MetaD)</h4>
                <p>
                  Gaussian hills of height <code className="text-slate-200">W₀</code> and width <code className="text-slate-200">σ</code> are deposited every <code className="text-slate-200">τ</code> steps.
                </p>
                <ul className="list-disc pl-4 space-y-1">
                  <li><strong>Standard MetaD:</strong> Hill height is constant (<code className="text-slate-200">W = W₀</code>). FES is estimated as: <code className="text-slate-200">F(x) = -V_B(x)</code>.</li>
                  <li><strong>Well-Tempered MetaD:</strong> Hill height decays exponentially as the energy well fills: <code className="text-slate-200">W(t) = W₀ exp(-V_B(x) / ΔT)</code> where <code className="text-slate-200">ΔT = T (γ - 1)</code>. FES is reconstructed as: <code className="text-slate-200">F(x) = - [γ / (γ - 1)] V_B(x)</code>.</li>
                </ul>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                <h4 className="font-bold text-purple-400">3. Custom Mathematical Functions</h4>
                <p>
                  You can define custom energy surfaces <code className="text-slate-200">V(x)</code> using arbitrary algebraic expressions (e.g. <code className="text-slate-200">0.5*(x^2-4)^2</code>, <code className="text-slate-200">3*cos(2*x)+0.15*x^4</code>).
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button 
                onClick={() => setShowGuideModal(false)}
                className="py-2 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs rounded-xl shadow-md"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default MetadynamicsLab;
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
  X
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

// --- Safe Array Min/Max Helper ---
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

// --- 1D PMF Plot Exporter matching Matplotlib PMF_subplots layout ---
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
  const height = 750;
  const padLeft = 110;
  const padRight = 60;
  const padTop = 115;
  const padBottom = 85;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const sVals = gridPoints.map((p) => p.s);
  const fesVals = gridPoints.map((p) => p.fes);

  const minS = Math.min(...sVals);
  const maxS = Math.max(...sVals);
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

  // 2. Plateau Position & Energy strictly inside current ROI grid points (rightmost 15% region)
  const plateauThresholdS = maxS - 0.15 * rangeS;
  const plateauPts = gridPoints.filter((p) => p.s >= plateauThresholdS);

  let plateauSumY = 0;
  let plateauSumX = 0;
  plateauPts.forEach((p) => {
    plateauSumY += p.fes;
    plateauSumX += p.s;
  });
  const platYVal = plateauPts.length > 0 ? plateauSumY / plateauPts.length : fesVals[fesVals.length - 1];
  const platXVal = plateauPts.length > 0 ? plateauSumX / plateauPts.length : maxS;

  const minY = Math.min(...fesVals);
  const maxY = Math.max(...fesVals);
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
  const plateauPy = padTop + plotH - ((platYVal - minY) / rangeY) * plotH;

  const bgColorAttr = transparent ? "none" : "#ffffff";
  const textColor = "#1e293b";
  const axisColor = "#334155";
  const gridColor = "#e2e8f0";

  // Exact Colors matching Matplotlib PMF_subplots
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

  // Build SVG XML matching Matplotlib plot
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

    <!-- Shaded DeltaG Region (Olive Green Fill) -->
    ${shadedPath ? `<path d="${shadedPath}" fill="${COLOR_PLATEAU_Y}" fill-opacity="0.20" />` : ""}

    <!-- Plateau Reference Horizontal Line (y = 0) -->
    <line x1="${padLeft}" y1="${zeroPy}" x2="${padLeft + plotW}" y2="${zeroPy}" stroke="black" stroke-width="1.5" stroke-dasharray="5,5" opacity="0.8" />

    <!-- Minimum Energy Dotted Horizontal Line -->
    <line x1="${padLeft}" y1="${minPy}" x2="${padLeft + plotW}" y2="${minPy}" stroke="${COLOR_PLATEAU_Y}" stroke-width="1.8" stroke-dasharray="2,3" opacity="0.9" />

    <!-- Minimum Position Vertical Line (Dark Red) -->
    <line x1="${minPx}" y1="${padTop}" x2="${minPx}" y2="${padTop + plotH}" stroke="${COLOR_MIN_X}" stroke-width="1.8" stroke-dasharray="6,4" />

    <!-- Bulk Position Vertical Line (Teal) -->
    <line x1="${bulkPx}" y1="${padTop}" x2="${bulkPx}" y2="${padTop + plotH}" stroke="${COLOR_PLATEAU_X}" stroke-width="1.8" stroke-dasharray="6,4" />

    <!-- PMF Curve Line (Dark Navy Blue) -->
    <polyline points="${pointsString}" fill="none" stroke="${COLOR_CURVE}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round" />

    <!-- Outer Frame Box -->
    <rect x="${padLeft}" y="${padTop}" width="${plotW}" height="${plotH}" fill="none" stroke="${axisColor}" stroke-width="2" />

    <!-- Text Annotations directly above lines matching Matplotlib -->
    <!-- Red Minimum Position Text -->
    <text x="${minPx}" y="${padTop + 24}" fill="${COLOR_MIN_X}" class="annot-text" text-anchor="middle">${minS_val.toFixed(2)}</text>

    <!-- Teal Plateau Position Text -->
    <text x="${bulkPx}" y="${padTop + 48}" fill="${COLOR_PLATEAU_X}" class="annot-text" text-anchor="middle">${platXVal.toFixed(2)}</text>

    <!-- Olive Plateau Energy Text floating above dotted line -->
    <text x="${padLeft + 35}" y="${plateauPy - 10}" fill="${COLOR_PLATEAU_Y}" class="annot-text" text-anchor="start">${Math.abs(minY).toFixed(2)}</text>

    <!-- Axis Titles -->
    <text x="${padLeft + plotW / 2}" y="${height - 20}" class="axis-label" text-anchor="middle">${cvName || "D.z"} (nm)</text>
    <text x="32" y="${padTop + plotH / 2}" class="axis-label" text-anchor="middle" transform="rotate(-90 32 ${padTop + plotH / 2})">Free Energy (${energyUnits})</text>

    <!-- Title Centered at Top -->
    <text x="${padLeft + plotW / 2}" y="${padTop - 14}" fill="#1e293b" font-family="Inter, sans-serif" font-size="24" font-weight="bold" text-anchor="middle">${cvName || "COV"}</text>

    <!-- Upper Right Badge Box (PAR-I) -->
    <g transform="translate(${padLeft + plotW - 95}, ${padTop + 15})">
      <rect x="0" y="0" width="80" height="32" rx="6" fill="white" stroke="#1e3a8a" stroke-width="1.2" />
      <text x="40" y="21" fill="#1e3a8a" font-family="Inter, sans-serif" font-size="15" font-weight="bold" text-anchor="middle">PAR-I</text>
    </g>

    <!-- Top Multicolumn Legend Box -->
    <g transform="translate(${padLeft + plotW / 2 - 340}, ${padTop - 60})">
      <rect x="0" y="0" width="680" height="34" rx="6" fill="white" stroke="#cbd5e1" stroke-width="1.2" />

      <!-- Item 1: PMF -->
      <line x1="20" y1="17" x2="50" y2="17" stroke="${COLOR_CURVE}" stroke-width="3" />
      <text x="58" y="21" class="legend-text">PMF</text>

      <!-- Item 2: Minimum (nm) -->
      <line x1="130" y1="17" x2="160" y2="17" stroke="${COLOR_MIN_X}" stroke-width="2" stroke-dasharray="5,3" />
      <text x="168" y="21" class="legend-text">Minimum (nm)</text>

      <!-- Item 3: Plateau pos. (nm) -->
      <line x1="320" y1="17" x2="350" y2="17" stroke="${COLOR_PLATEAU_X}" stroke-width="2" stroke-dasharray="5,3" />
      <text x="358" y="21" class="legend-text">Plateau pos. (nm)</text>

      <!-- Item 4: Plateau energy (kJ/mol) -->
      <line x1="510" y1="17" x2="540" y2="17" stroke="${COLOR_PLATEAU_Y}" stroke-width="2" stroke-dasharray="2,2" />
      <text x="548" y="21" class="legend-text">Plateau energy (${energyUnits})</text>
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

// --- Inline Web Worker Creator supporting 1D and 2D HILLS ---
function createHillsWorker() {
  const code = `
  self.onmessage = function(e) {
    const text = e.data.text;
    const numBinsUser = e.data.numBins || 300;
    const isWtScaling = e.data.isWtScaling !== false;
    const customBiasFactor = e.data.customBiasFactor;
    const energyUnits = e.data.energyUnits || "kJ/mol";
    const gridMinUser = e.data.gridMinUser;
    const gridMaxUser = e.data.gridMaxUser;

    if (!text || typeof text !== "string") {
      self.postMessage({ error: "File is empty or invalid text." });
      return;
    }

    const lines = text.split("\\n");
    const totalLines = lines.length;
    let fieldNames = [];
    let headerMeta = {};
    const dataRows = [];

    for (let i = 0; i < totalLines; i++) {
      const rawLine = lines[i].trim();
      if (!rawLine) continue;

      if (rawLine.startsWith("#!")) {
        const parts = rawLine.replace("#!", "").trim().split(/\\s+/);
        const key = parts[0]?.toUpperCase();

        if (key === "FIELDS") {
          fieldNames = parts.slice(1);
        } else if (key === "SET") {
          if (parts.length >= 3) {
            headerMeta[parts[1]] = parts[2];
          }
        }
        continue;
      }

      if (rawLine.startsWith("#")) continue;

      const tokens = rawLine.split(/\\s+/).map((v) => parseFloat(v));
      if (tokens.length === 0 || tokens.some((val) => isNaN(val))) continue;
      dataRows.push(tokens);

      if (i % 30000 === 0) {
        self.postMessage({ progress: Math.min(40, Math.floor((i / totalLines) * 40)) });
      }
    }

    if (dataRows.length === 0) {
      self.postMessage({ error: "No valid numeric data rows found in HILLS file." });
      return;
    }

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

    const parsedHills = dataRows.map((row, rowIdx) => {
      const timeVal = row[timeIdx] ?? rowIdx * 10;
      const heightVal = row[heightIdx] ?? 1.0;
      const biasfVal = biasfIdx !== -1 && biasfIdx < row.length ? row[biasfIdx] : null;

      const cvVals = cvIndices.map((ci) => row[ci] ?? 0.0);
      const sigmaVals = sigmaIndices.map((si) => row[si] ?? 0.1);

      return {
        step: rowIdx + 1,
        time: timeVal,
        cvs: cvVals,
        sigmas: sigmaVals,
        height: heightVal,
        biasf: biasfVal
      };
    });

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

    const numFrames = 100;
    const timelineGrids = new Array(numFrames);
    const chunkHillsCount = Math.ceil(parsedHills.length / numFrames);

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

      for (let f = 0; f < numFrames; f++) {
        const startH = f * chunkHillsCount;
        const endH = Math.min(parsedHills.length, (f + 1) * chunkHillsCount);

        for (let h = startH; h < endH; h++) {
          const hill = parsedHills[h];
          const center = hill.cvs[0];
          const sigma = hill.sigmas[0] || avgSigma;
          const height = hill.height;
          if (height === 0 || sigma === 0) continue;
          const invTwoSigmaSq = 1.0 / (2 * sigma * sigma);

          for (let i = 0; i < numBins; i++) {
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
          frameIndex: f + 1,
          pct: Math.min(100, Math.round(((f + 1) / numFrames) * 100)),
          sampleTime: parsedHills[Math.min(parsedHills.length - 1, endH - 1)]?.time || 0,
          activeHillsCount: endH,
          gridPoints: frameGrid
        };

        if (f % 10 === 0) {
          self.postMessage({ progress: 50 + Math.floor((f / numFrames) * 50) });
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

      for (let f = 0; f < numFrames; f++) {
        const startH = f * chunkHillsCount;
        const endH = Math.min(parsedHills.length, (f + 1) * chunkHillsCount);

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

          for (let j = 0; j < numBinsY; j++) {
            const y = gridMin2 + j * stepY;
            const diffy = y - cy;
            const termY = (diffy * diffy) * inv2SigYSq;
            const rowOffset = j * numBinsX;

            for (let i = 0; i < numBinsX; i++) {
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

        timelineGrids[f] = {
          frameIndex: f + 1,
          pct: Math.min(100, Math.round(((f + 1) / numFrames) * 100)),
          sampleTime: parsedHills[Math.min(parsedHills.length - 1, endH - 1)]?.time || 0,
          activeHillsCount: endH,
          grid2DFlat,
          numBinsX,
          numBinsY,
          gridMin1,
          gridMax1,
          gridMin2,
          gridMax2
        };

        if (f % 10 === 0) {
          self.postMessage({ progress: 50 + Math.floor((f / numFrames) * 50) });
        }
      }
    }

    self.postMessage({
      result: {
        headerMeta,
        fieldNames,
        cvNames,
        is2D,
        hills: parsedHills,
        totalHills: parsedHills.length,
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
  const [showTrajectory, setShowTrajectory] = useState(true);

  const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

  useEffect(() => {
    if (!frameData || !frameData.grid2DFlat || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat } = frameData;
    const width = canvas.width;
    const height = canvas.height;

    const padLeft = 60;
    const padRight = 75;
    const padTop = 25;
    const padBottom = 45;

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

      ctx.fillText(xVal.toFixed(0), px, padTop + plotH + 18);
    }

    ctx.fillStyle = "#f1f5f9";
    ctx.font = "bold 12px Inter, sans-serif";
    ctx.fillText(`${cvNames[0] || "CV1"} Coordinate`, padLeft + plotW / 2, height - 8);

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

    const barX = padLeft + plotW + 20;
    const barY = padTop;
    const barW = 16;
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
    ctx.fillText(`F [${energyUnits}]`, barX, barY - 8);

    if (showTrajectory && hills && hills.length > 0) {
      const activeHills = hills.slice(0, frameData.activeHillsCount);
      if (activeHills.length > 0) {
        ctx.beginPath();
        ctx.strokeStyle = "rgba(56, 189, 248, 0.65)";
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
        ctx.fillStyle = "#00f0ff";
        ctx.shadowColor = "#00f0ff";
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }
  }, [frameData, energyRefMode, energyUnits, cvNames, hills, colorPalette, showTrajectory]);

  const handleMouseMove = (e) => {
    if (!canvasRef.current || !frameData || !frameData.grid2DFlat) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const padLeft = 60;
    const padRight = 75;
    const padTop = 25;
    const padBottom = 45;
    const width = canvasRef.current.width;
    const height = canvasRef.current.height;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    if (x < padLeft || x > width - padRight || y < padTop || y > height - padBottom) {
      setHoverInfo(null);
      return;
    }

    const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat } = frameData;

    const normX = (x - padLeft) / plotW;
    const normY = (height - padBottom - y) / plotH;

    const cv1Val = gridMin1 + normX * (gridMax1 - gridMin1);
    const cv2Val = gridMin2 + normY * (gridMax2 - gridMin2);

    const binI = Math.min(numBinsX - 1, Math.max(0, Math.floor(normX * numBinsX)));
    const binJ = Math.min(numBinsY - 1, Math.max(0, Math.floor(normY * numBinsY)));

    const idx = binJ * numBinsX + binI;
    const rawVal = energyRefMode !== "raw" ? grid2DFlat[idx * 2 + 1] : grid2DFlat[idx * 2];
    const fesVal = parseFloat((rawVal * unitScale).toFixed(3));

    setHoverInfo({
      x,
      y,
      cv1: cv1Val.toFixed(3),
      cv2: cv2Val.toFixed(3),
      fes: fesVal
    });
  };

  return (
    <div className="flex flex-col items-center space-y-4 relative w-full">
      <div className="flex flex-wrap justify-between items-center w-full px-1 text-xs gap-2">
        <label className="flex items-center gap-2 cursor-pointer bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all text-slate-300">
          <input
            type="checkbox"
            checked={showTrajectory}
            onChange={(e) => setShowTrajectory(e.target.checked)}
            className="accent-cyan-500 rounded"
          />
          <span className="font-semibold">Show Trajectory Overlay</span>
        </label>

        {hoverInfo ? (
          <div className="flex items-center gap-3 font-mono text-xs bg-slate-950/90 px-3 py-1.5 rounded-xl border border-indigo-500/40 shadow-lg">
            <span className="text-slate-300">{cvNames[0] || "CV1"}: <strong className="text-cyan-300">{hoverInfo.cv1}</strong></span>
            <span className="text-slate-300">{cvNames[1] || "CV2"}: <strong className="text-purple-300">{hoverInfo.cv2}</strong></span>
            <span className="text-rose-400 font-bold">F(s₁,s₂): {hoverInfo.fes} {energyUnits}</span>
          </div>
        ) : (
          <span className="text-[11px] text-slate-400 font-mono italic">Hover over heatmap for energy inspection</span>
        )}
      </div>

      <div className="relative border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-950 p-2">
        <canvas
          ref={canvasRef}
          width={640}
          height={440}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverInfo(null)}
          className="cursor-crosshair block rounded-xl"
        />

        {hoverInfo && (
          <div
            className="absolute pointer-events-none border border-cyan-400/60 rounded-full w-5 h-5 -translate-x-1/2 -translate-y-1/2 shadow-lg shadow-cyan-500/50"
            style={{ left: hoverInfo.x + 8, top: hoverInfo.y + 8 }}
          >
            <div className="w-1 h-1 bg-cyan-400 rounded-full absolute inset-0 m-auto"></div>
          </div>
        )}
      </div>
    </div>
  );
}

function HillsVisualizerInner() {
  const [hillsData, setHillsData] = useState(null);
  const [fileName, setFileName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [isDraggingFile, setIsDraggingFile] = useState(false);

  const [activeTab, setActiveTab] = useState("fes");
  const [colorPalette, setColorPalette] = useState("Viridis");

  // Export Modal State
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState("png");
  const [exportTransparent, setExportTransparent] = useState(false);

  // Interactive Mouse Box Zoom State
  const [refAreaLeft, setRefAreaLeft] = useState("");
  const [refAreaRight, setRefAreaRight] = useState("");

  // Applied parameters used for computation
  const [numBins, setNumBins] = useState(300);
  const [customBiasFactor, setCustomBiasFactor] = useState("");
  const [gridMinUser, setGridMinUser] = useState("");
  const [gridMaxUser, setGridMaxUser] = useState("");

  // Local draft inputs for user editing
  const [inputNumBins, setInputNumBins] = useState("300");
  const [inputCustomBias, setInputCustomBias] = useState("");
  const [inputGridMin, setInputGridMin] = useState("");
  const [inputGridMax, setInputGridMax] = useState("");

  const [timeStepProgress, setTimeStepProgress] = useState(100);
  const [isPlayingTime, setIsPlayingTime] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(60);

  const [energyUnits, setEnergyUnits] = useState("kJ/mol");
  const [energyRefMode, setEnergyRefMode] = useState("plateauZero"); // "raw" | "minZero" | "plateauZero"
  const [isWtScaling, setIsWtScaling] = useState(true);

  const fileInputRef = useRef(null);
  const rawTextRef = useRef("");
  const currentFileNameRef = useRef("");
  const isMounting = useRef(true);

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

        setGridMinUser(minStr);
        setGridMaxUser(maxStr);
        setInputGridMin(minStr);
        setInputGridMax(maxStr);
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
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        processHillsText(text, file.name);
        setTimeStepProgress(100);
        setIsPlayingTime(false);
      };
      reader.readAsText(file);
    }
  };

  // Time Slider Animation Loop (Smooth 60 FPS Playback)
  useEffect(() => {
    let timer = null;
    if (isPlayingTime) {
      timer = setInterval(() => {
        setTimeStepProgress((prev) => {
          if (prev >= 100) {
            return 1;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isPlayingTime, playbackSpeed]);

  // Execute Background Web Worker Parsing & Pre-computation
  const processHillsText = (text, name) => {
    if (!text) return;
    rawTextRef.current = text;
    currentFileNameRef.current = name || fileName || "HILLS";

    setErrorMsg("");
    setIsLoading(true);
    setLoadingProgress(5);
    setLoadingMsg(`Processing "${currentFileNameRef.current}" in Web Worker...`);

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
        worker.terminate();
      }
    };

    worker.onerror = (err) => {
      console.error("Worker error:", err);
      setErrorMsg("Error in background Web Worker processor.");
      setIsLoading(false);
      worker.terminate();
    };

    worker.postMessage({
      text,
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
    if (rawTextRef.current) {
      processHillsText(rawTextRef.current, currentFileNameRef.current);
    }
  }, [numBins, isWtScaling, customBiasFactor, gridMinUser, gridMaxUser]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target.result;
      processHillsText(text, file.name);
      setTimeStepProgress(100);
      setIsPlayingTime(false);
    };
    reader.readAsText(file);
    e.target.value = null;
  };

  const handleApplyGridParams = (e) => {
    if (e) e.preventDefault();
    setNumBins(parseInt(inputNumBins) || 300);
    setCustomBiasFactor(inputCustomBias);
    setGridMinUser(inputGridMin);
    setGridMaxUser(inputGridMax);
  };

  const handleResetGridBounds = () => {
    setInputGridMin("");
    setInputGridMax("");
    setGridMinUser("");
    setGridMaxUser("");
  };

  const currentFrameData = useMemo(() => {
    if (!hillsData || !hillsData.timelineGrids || hillsData.timelineGrids.length === 0) return null;
    const idx = Math.max(0, Math.min(99, timeStepProgress - 1));
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

      // Calculate bulk plateau energy level strictly inside active ROI (rightmost 15% region)
      const plateauThresholdS = activePts[activePts.length - 1].s - 0.15 * (activePts[activePts.length - 1].s - activePts[0].s || 1);
      const plateauPts = activePts.filter((p) => p.s >= plateauThresholdS);

      let bulkSum = 0;
      let bulkCount = 0;
      let bulkSumX = 0;
      for (let b = 0; b < plateauPts.length; b++) {
        bulkSum += plateauPts[b].rawFes;
        bulkSumX += plateauPts[b].s;
        bulkCount++;
      }
      const bulkFes = bulkCount > 0 ? bulkSum / bulkCount : activePts[activePts.length - 1].rawFes;
      const bulkS = bulkCount > 0 ? bulkSumX / bulkCount : activePts[activePts.length - 1].s;

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

  const chartCvData = useMemo(() => {
    if (!hillsData || !hillsData.hills) return [];
    const raw = hillsData.hills.map((h) => ({
      time: h.time,
      cv1: h.cvs[0],
      cv2: hillsData.is2D ? h.cvs[1] : undefined
    }));
    return downsampleArray(raw, 800);
  }, [hillsData]);

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
        `#! BiasFactor: ${hillsData.effectiveBiasFactor}`,
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
      className="flex flex-col w-full max-w-7xl mx-auto space-y-6 relative min-h-[75vh]"
    >
      {/* Export Plot Options Modal (Temporarily Deactivated) */}
      {false && showExportModal && currentFrameData?.gridPoints && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl max-w-md w-full space-y-5 relative">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ImageIcon size={18} className="text-cyan-400" />
                Download 1D PMF Plot
              </h3>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-slate-400 hover:text-white font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs">
              {(gridMinUser || gridMaxUser) && (
                <div className="bg-cyan-950/80 border border-cyan-700/60 p-2.5 rounded-xl text-cyan-300 font-mono flex items-center justify-between text-[11px]">
                  <span>Active Zoom ROI: [{gridMinUser || "Auto"}, {gridMaxUser || "Auto"}]</span>
                  <span className="text-cyan-400 font-bold">ROI Filter Enabled</span>
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1.5">File Format:</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setExportFormat("png")}
                    className={`py-2 px-3 rounded-xl font-bold border transition-all ${
                      exportFormat === "png"
                        ? "bg-cyan-500 text-slate-950 border-cyan-400"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    PNG (Image)
                  </button>
                  <button
                    type="button"
                    onClick={() => setExportFormat("svg")}
                    className={`py-2 px-3 rounded-xl font-bold border transition-all ${
                      exportFormat === "svg"
                        ? "bg-cyan-500 text-slate-950 border-cyan-400"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    SVG (Vector)
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1.5">Background Style:</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setExportTransparent(false)}
                    className={`py-2 px-3 rounded-xl font-bold border transition-all ${
                      !exportTransparent
                        ? "bg-indigo-600 text-white border-indigo-400"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    Solid White (#FFFFFF)
                  </button>
                  <button
                    type="button"
                    onClick={() => setExportTransparent(true)}
                    className={`py-2 px-3 rounded-xl font-bold border transition-all ${
                      exportTransparent
                        ? "bg-indigo-600 text-white border-indigo-400"
                        : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white"
                    }`}
                  >
                    Transparent
                  </button>
                </div>
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => {
                  export1DPlot({
                    gridPoints: currentFrameData.gridPoints,
                    cvName: hillsData.cvNames[0] || "D.z",
                    energyUnits,
                    energyRefMode,
                    format: exportFormat,
                    transparent: exportTransparent
                  });
                  setShowExportModal(false);
                }}
                className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
              >
                <Download size={16} /> Download {exportFormat.toUpperCase()} Plot
              </button>
            </div>
          </div>
        </div>
      )}

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

      {/* EMPTY STATE PLACEHOLDER (When no HILLS file is loaded) */}
      {!hillsData && !isLoading && (
        <div className="bg-slate-900/90 backdrop-blur-xl border-2 border-dashed border-slate-800 hover:border-indigo-500/50 rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-6 shadow-2xl transition-all my-8">
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

      {/* Key Metrics Cards Dashboard */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 shadow-md flex flex-col justify-between">
            <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
              <Layers size={13} className="text-indigo-400" /> Gaussian Hills
            </span>
            <span className="text-xl font-extrabold text-white mt-1 font-mono">
              {stats.totalHills}
            </span>
            <span className="text-[10px] text-slate-500 mt-0.5">{stats.is2D ? "2D Gaussian Hills" : "1D Gaussian Hills"}</span>
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
              className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                activeTab === "fes"
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <TrendingUp size={15} /> Free Energy Surface F(s)
            </button>

            <button
              onClick={() => setActiveTab("height")}
              className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                activeTab === "height"
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Zap size={15} /> Height Decay W(t)
            </button>

            <button
              onClick={() => setActiveTab("cv")}
              className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                activeTab === "cv"
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Activity size={15} /> CV Trajectory s(t)
            </button>
          </div>

          {/* File Name Tag */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-950/80 rounded-xl border border-slate-800 text-xs font-mono text-slate-300">
            <FileText size={14} className="text-indigo-400" />
            <span>{fileName || "No file loaded"}</span>
          </div>
        </div>
      )}

      {/* MAIN TAB CONTENT */}
      {hillsData && activeTab === "fes" && currentFrameData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Main Chart Area */}
          <div className="lg:col-span-8 bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            
            <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-2">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <TrendingUp size={18} className="text-indigo-400" />
                  {hillsData.is2D ? "Reconstructed 2D Free Energy Heatmap F(s₁, s₂)" : "Reconstructed Free Energy Profile F(s)"}
                </h2>
                <p className="text-slate-400 text-xs">
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
                    <option value="Viridis">Viridis (Scientific Default)</option>
                    <option value="Inferno">Inferno (Thermal Glow)</option>
                    <option value="Spectral">Spectral (Rainbow)</option>
                    <option value="CoolWarm">Cool-Warm (Blue-Red)</option>
                  </select>
                )}

                {/* Download Plot (PNG/SVG) Button (Temporarily Deactivated) */}
                {false && !hillsData.is2D && (
                  <button
                    onClick={() => setShowExportModal(true)}
                    className="px-3 py-1.5 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/60 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                    title="Download 1D PMF Plot (PNG/SVG)"
                  >
                    <ImageIcon size={14} /> Download Plot (PNG/SVG)
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

            {/* 1D AreaChart vs 2D Heatmap Canvas */}
            {!hillsData.is2D ? (
              <div className="h-80 w-full pt-2 select-none">
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
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{
                        value: `Collective Variable (${hillsData.cvNames[0] || "CV1"})`,
                        position: "insideBottom",
                        offset: -12,
                        fill: "#cbd5e1",
                        fontSize: 12
                      }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      domain={['auto', 'auto']}
                      label={{
                        value: `Free Energy F(s) [${energyUnits}]`,
                        angle: -90,
                        position: "insideLeft",
                        offset: 10,
                        fill: "#cbd5e1",
                        fontSize: 12
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
                      strokeWidth={2.5}
                      fill="url(#fesGradient)"
                      isAnimationActive={false}
                    />

                    {/* Reference Lines when Bulk Plateau mode is active */}
                    {energyRefMode === "plateauZero" && currentFrameData?.bulkS !== undefined && (
                      <>
                        {/* Horizontal Plateau Reference Line (y = 0) */}
                        <ReferenceLine
                          y={0}
                          stroke="#cbd5e1"
                          strokeWidth={1.5}
                          strokeDasharray="5 5"
                          label={{ value: "Plateau (y=0)", fill: "#cbd5e1", fontSize: 11, position: "top" }}
                        />

                        {/* Vertical Plateau Measured Position Line (Teal #2B8092) */}
                        <ReferenceLine
                          x={currentFrameData.bulkS}
                          stroke="#2B8092"
                          strokeWidth={1.5}
                          strokeDasharray="6 4"
                          label={{ value: "Plateau Position", fill: "#2B8092", fontSize: 11, position: "insideTopRight" }}
                        />
                      </>
                    )}

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

            {/* Time Trajectory Progress Slider with Smooth REAL-TIME PLAY / PAUSE */}
            <div className="bg-slate-950/80 border border-slate-800/80 p-4 rounded-xl space-y-3">
              <div className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsPlayingTime(!isPlayingTime)}
                    className={`py-1.5 px-3.5 rounded-xl font-bold text-xs shadow-md flex items-center gap-1.5 transition-all ${
                      isPlayingTime
                        ? "bg-amber-500 text-slate-950 hover:bg-amber-400 shadow-amber-500/20"
                        : "bg-emerald-500 text-slate-950 hover:bg-emerald-400 shadow-emerald-500/20"
                    }`}
                  >
                    {isPlayingTime ? <><Pause size={14} /> PAUSE</> : <><Play size={14} /> PLAY</>}
                  </button>

                  <button
                    onClick={() => setTimeStepProgress(1)}
                    className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-400 rounded-lg border border-slate-800"
                    title="Reset to 1%"
                  >
                    <RotateCcw size={14} />
                  </button>
                </div>

                <span className="font-mono text-cyan-400 font-bold text-xs">
                  {timeStepProgress}% (t = {currentFrameData.sampleTime.toFixed(1)} ps • {currentFrameData.activeHillsCount} hills)
                </span>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={timeStepProgress}
                  onChange={(e) => setTimeStepProgress(parseInt(e.target.value))}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>0 ps (Start)</span>
                <span>50%</span>
                <span>{hillsData.timeRange[1].toFixed(0)} ps (End)</span>
              </div>
            </div>

          </div>

          {/* Controls & Configuration Panel */}
          <div className="lg:col-span-4 space-y-5">
            
            {/* Display Mode Switcher Card */}
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2.5 border-b border-slate-800/80 pb-3 pt-0.5">
                <Sliders size={15} className="text-indigo-400" />
                Energy Display Mode
              </h3>

              <div className="space-y-2 text-xs">
                <label className="flex items-start justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all gap-2">
                  <div>
                    <div className="font-semibold text-slate-200">Bulk Plateau Reference [F(bulk) = 0]</div>
                    <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                      Sets bulk solvent energy to 0, minimum well depth is -ΔG
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="energyRef"
                    checked={energyRefMode === "plateauZero"}
                    onChange={() => setEnergyRefMode("plateauZero")}
                    className="accent-indigo-500 mt-1"
                  />
                </label>

                <label className="flex items-start justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all gap-2">
                  <div>
                    <div className="font-semibold text-slate-200">Relative to Minimum [F(min) = 0]</div>
                    <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                      Sets minimum bound well to 0, bulk plateau is +ΔG
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="energyRef"
                    checked={energyRefMode === "minZero"}
                    onChange={() => setEnergyRefMode("minZero")}
                    className="accent-indigo-500 mt-1"
                  />
                </label>

                <label className="flex items-start justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all gap-2">
                  <div>
                    <div className="font-semibold text-slate-200">Direct Absolute Potential [F(s) = -V(s)]</div>
                    <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                      Raw unshifted cumulative bias potential
                    </div>
                  </div>
                  <input
                    type="radio"
                    name="energyRef"
                    checked={energyRefMode === "raw"}
                    onChange={() => setEnergyRefMode("raw")}
                    className="accent-indigo-500 mt-1"
                  />
                </label>
              </div>

              <div className="pt-1">
                <label className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all text-xs">
                  <span className="font-semibold text-slate-300">
                    Well-Tempered Scaling Factor [γ/(γ-1)]
                  </span>
                  <input
                    type="checkbox"
                    checked={isWtScaling}
                    onChange={(e) => setIsWtScaling(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                </label>
              </div>
            </div>

            {/* Grid & Calculation Settings Form */}
            <form onSubmit={handleApplyGridParams} className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5.5 sm:p-6 shadow-2xl space-y-4">
              <h3 className="font-bold text-sm text-white flex items-center gap-2.5 border-b border-slate-800/80 pb-3 pt-0.5">
                <Sliders size={16} className="text-indigo-400" />
                FES Grid Parameters
              </h3>

              {!hillsData?.is2D && (
                <div>
                  <label className="block text-xs text-slate-400 mb-1 font-medium">
                    Grid Resolution (Bins):
                  </label>
                  <input
                    type="number"
                    min="50"
                    max="1000"
                    value={inputNumBins}
                    onChange={(e) => setInputNumBins(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-cyan-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">
                  Well-Tempered Bias Factor (γ):
                </label>
                <input
                  type="text"
                  placeholder={`Detected: ${hillsData?.effectiveBiasFactor}`}
                  value={inputCustomBias}
                  onChange={(e) => setInputCustomBias(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-indigo-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1 font-medium">
                  Energy Units:
                </label>
                <select
                  value={energyUnits}
                  onChange={(e) => setEnergyUnits(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 outline-none"
                >
                  <option value="kJ/mol">kJ/mol</option>
                  <option value="kcal/mol">kcal/mol</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-1">
                <div>
                  <label className="block text-[10px] text-slate-400 mb-1">Min CV1 Bound:</label>
                  <input
                    type="text"
                    placeholder="Auto"
                    value={inputGridMin}
                    onChange={(e) => setInputGridMin(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-slate-400 mb-1">Max CV1 Bound:</label>
                  <input
                    type="text"
                    placeholder="Auto"
                    value={inputGridMax}
                    onChange={(e) => setInputGridMax(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                  />
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  className="flex-1 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 shadow-md"
                >
                  <RefreshCw size={14} /> Apply Parameters
                </button>

                <button
                  type="button"
                  onClick={handleResetGridBounds}
                  className="px-3 py-2 bg-slate-950 hover:bg-slate-800 text-slate-400 border border-slate-800 rounded-xl text-xs font-semibold"
                  title="Reset CV Bounds to Auto"
                >
                  <RotateCcw size={14} />
                </button>
              </div>

            </form>

          </div>

        </div>
      )}

      {/* TAB 2: Gaussian Height Decay W(t) */}
      {hillsData && activeTab === "height" && (
        <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap size={18} className="text-amber-400" />
              Gaussian Height Decay W(t) (WT-Metadynamics)
            </h2>
            <p className="text-slate-400 text-xs">
              Evolution of deposited hill heights across the simulation
            </p>
          </div>

          <div className="h-96 w-full pt-2">
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

      {/* TAB 3: Collective Variable Trajectory s(t) */}
      {hillsData && activeTab === "cv" && (
        <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity size={18} className="text-emerald-400" />
              {hillsData.is2D ? "Collective Variables Trajectory (CV1, CV2) Over Time" : "Collective Variable Trajectory s(t) Over Time"}
            </h2>
            <p className="text-slate-400 text-xs">
              Shows system diffusion along the reaction coordinate(s) and barrier crossing events.
            </p>
          </div>

          <div className="h-96 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartCvData}
                margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="time"
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  label={{ value: "Time (ps)", position: "insideBottom", offset: -12, fill: "#cbd5e1", fontSize: 12 }}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />

                <Line
                  type="monotone"
                  dataKey="cv1"
                  name={hillsData.cvNames[0] || "CV1"}
                  stroke="#34d399"
                  strokeWidth={1.5}
                  dot={false}
                />

                {hillsData.is2D && (
                  <Line
                    type="monotone"
                    dataKey="cv2"
                    name={hillsData.cvNames[1] || "CV2"}
                    stroke="#a855f7"
                    strokeWidth={1.5}
                    dot={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

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
cp "../HILLS" src/HILLS_SAMPLE 2>/dev/null || true
python3 -c "
import os
sample_path = 'src/HILLS_SAMPLE' if os.path.exists('src/HILLS_SAMPLE') else '../HILLS'
try:
    with open(sample_path) as f:
        content = f.read()
    with open('src/sampleHills.js', 'w') as f:
        f.write('export const SAMPLE_HILLS_TEXT = ' + repr(content) + ';\n')
except Exception as e:
    with open('src/sampleHills.js', 'w') as f:
        f.write('export const SAMPLE_HILLS_TEXT = \"\";\n')
" 2>/dev/null || true

echo "=== Writing src/App.jsx ==="
cat << 'EOF' > src/App.jsx
import React, { useState } from "react";
import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";
import MetadynamicsLab2D from "./MetadynamicsLab2D";
import HillsVisualizer from "./HillsVisualizer";
import { Activity, Layers, BarChart2 } from "lucide-react";

function App() {
  const [simDimension, setSimDimension] = useState("1D");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6 px-4 sm:px-6 lg:px-8 selection:bg-cyan-500 selection:text-white relative overflow-x-hidden">
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto mb-5 flex flex-wrap justify-between items-center bg-slate-900/90 backdrop-blur-md p-2 rounded-2xl border border-slate-800 shadow-xl gap-3">
        <div className="flex items-center gap-2 pl-3">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Metadynamics Mode:
          </span>
        </div>
        
        <div className="flex flex-wrap bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setSimDimension("1D")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              simDimension === "1D"
                ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity size={15} /> Simulador 1D (CV_x)
          </button>
          
          <button
            onClick={() => setSimDimension("2D")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              simDimension === "2D"
                ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers size={15} /> Simulador 2D (CV_x, CV_y)
          </button>

          <button
            onClick={() => setSimDimension("HILLS")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              simDimension === "HILLS"
                ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <BarChart2 size={15} /> Visualizador HILLS (PLUMED)
          </button>
        </div>
      </div>

      {simDimension === "1D" ? (
        <MetadynamicsLab />
      ) : simDimension === "2D" ? (
        <MetadynamicsLab2D />
      ) : (
        <HillsVisualizer />
      )}
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

echo "=== Done ==="
echo "Project $PROJECT_NAME created successfully."
echo "1) cd $PROJECT_NAME"
echo "2) npm run dev"
