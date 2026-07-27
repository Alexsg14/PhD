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