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
