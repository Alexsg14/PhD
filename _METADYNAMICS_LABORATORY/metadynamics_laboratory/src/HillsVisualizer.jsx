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
  RefreshCw
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
  Area
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

// --- Inline Web Worker Creator ---
function createHillsWorker() {
  const code = `
  self.onmessage = function(e) {
    const text = e.data.text;
    const numBins = e.data.numBins || 300;
    const isWtScaling = e.data.isWtScaling !== false;
    const customBiasFactor = e.data.customBiasFactor;
    const isZeroRefMode = !!e.data.isZeroRefMode;
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
    if (biasfIdx === -1 && fieldNames.length >= 5) {
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

    const cvNames = cvIndices.map((idx) => fieldNames[idx] || ("CV" + idx));
    const startTime = parsedHills[0]?.time ?? 0;
    const endTime = parsedHills[parsedHills.length - 1]?.time ?? 0;

    // Calculate grid range
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

    let gamma = 1.0;
    if (customBiasFactor !== "" && !isNaN(parseFloat(customBiasFactor))) {
      gamma = parseFloat(customBiasFactor);
    } else if (parsedHills[0]?.biasf !== null && parsedHills[0]?.biasf > 1) {
      gamma = parsedHills[0].biasf;
    }
    const wtFactor = isWtScaling && gamma > 1 ? gamma / (gamma - 1) : 1.0;
    const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

    // Precalculate 100 incremental timeline frames for 60FPS real-time playback
    const numFrames = 100;
    const timelineGrids = new Array(numFrames);
    const chunkHillsCount = Math.ceil(parsedHills.length / numFrames);
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

      // Convert accumulated V to FES grid points for frame f
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
        const rawFesVal = rawF[i];
        const zeroFesVal = rawF[i] - minFES;

        frameGrid[i] = {
          s: parseFloat(s.toFixed(4)),
          rawFes: rawFesVal,
          zeroFes: zeroFesVal,
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

    self.postMessage({
      result: {
        headerMeta,
        fieldNames,
        cvNames,
        is2D: cvIndices.length >= 2,
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

function HillsVisualizerInner() {
  const [hillsData, setHillsData] = useState(null);
  const [fileName, setFileName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingMsg, setLoadingMsg] = useState("");
  const [isDraggingFile, setIsDraggingFile] = useState(false);

  const [activeTab, setActiveTab] = useState("fes"); // "fes" | "height" | "cv" | "convergence"

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

  const [timeStepProgress, setTimeStepProgress] = useState(100); // 1 to 100% of trajectory
  const [isPlayingTime, setIsPlayingTime] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(60); // ms per frame

  const [energyUnits, setEnergyUnits] = useState("kJ/mol"); // "kJ/mol" | "kcal/mol"
  const [isZeroRefMode, setIsZeroRefMode] = useState(false); // false = Direct Absolute F(s)=-V(s), true = Relative F(s) min=0
  const [isWtScaling, setIsWtScaling] = useState(true); // apply gamma/(gamma-1) factor

  const fileInputRef = useRef(null);
  const rawTextRef = useRef("");
  const currentFileNameRef = useRef("");
  const isMounting = useRef(true);

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
            return 1; // loop back
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
      isZeroRefMode,
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

  // Explicit Update Button Handler for Grid Parameters
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

  // Dynamically formatted grid points for active frame
  const currentFrameData = useMemo(() => {
    if (!hillsData || !hillsData.timelineGrids || hillsData.timelineGrids.length === 0) return null;
    const idx = Math.max(0, Math.min(99, timeStepProgress - 1));
    const rawFrame = hillsData.timelineGrids[idx];
    if (!rawFrame || !rawFrame.gridPoints) return null;

    const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

    const formattedPoints = rawFrame.gridPoints.map((p) => {
      const rawVal = isZeroRefMode ? p.zeroFes : p.rawFes;
      return {
        s: p.s,
        fes: parseFloat((rawVal * unitScale).toFixed(3)),
        vBias: parseFloat((p.vBiasRaw * unitScale).toFixed(3))
      };
    });

    return {
      ...rawFrame,
      gridPoints: formattedPoints
    };
  }, [hillsData, timeStepProgress, isZeroRefMode, energyUnits]);

  // Multi-stage convergence rows
  const convergenceData = useMemo(() => {
    if (!hillsData || !hillsData.timelineGrids || hillsData.timelineGrids.length < 100) {
      return { chartRows: [] };
    }
    const unitScale = energyUnits === "kcal/mol" ? 0.239006 : 1.0;

    const g25 = hillsData.timelineGrids[24].gridPoints;
    const g50 = hillsData.timelineGrids[49].gridPoints;
    const g75 = hillsData.timelineGrids[74].gridPoints;
    const g100 = hillsData.timelineGrids[99].gridPoints;

    const chartRows = [];
    for (let i = 0; i < g100.length; i++) {
      const getVal = (pt) => {
        if (!pt) return 0;
        const raw = isZeroRefMode ? pt.zeroFes : pt.rawFes;
        return parseFloat((raw * unitScale).toFixed(3));
      };

      chartRows.push({
        s: g100[i].s,
        "FES_25%": getVal(g25[i]),
        "FES_50%": getVal(g50[i]),
        "FES_75%": getVal(g75[i]),
        "FES_100%": getVal(g100[i])
      });
    }
    return { chartRows };
  }, [hillsData, isZeroRefMode, energyUnits]);

  // Downsampled datasets for Recharts line charts
  const chartHeightData = useMemo(() => {
    if (!hillsData || !hillsData.hills) return [];
    return downsampleArray(hillsData.hills, 800);
  }, [hillsData]);

  const chartCvData = useMemo(() => {
    if (!hillsData || !hillsData.hills) return [];
    const raw = hillsData.hills.map((h) => ({ time: h.time, cv: h.cvs[0] }));
    return downsampleArray(raw, 800);
  }, [hillsData]);

  // Overall Statistics Summary
  const stats = useMemo(() => {
    if (!hillsData || !hillsData.hills || hillsData.hills.length === 0) return null;
    const hills = hillsData.hills;

    const initialHeight = hills[0].height;
    const finalHeight = hills[hills.length - 1].height;
    const heightReductionRatio =
      initialHeight > 0
        ? (((initialHeight - finalHeight) / initialHeight) * 100).toFixed(1)
        : "0.0";

    const cvVals = hills.map((h) => h.cvs[0]);
    const { min: minCVNum, max: maxCVNum } = getMinMax(cvVals, 0);

    return {
      totalHills: hillsData.totalHills,
      totalTime: hillsData.timeRange[1].toFixed(1),
      stride: hillsData.stride.toFixed(1),
      initialHeight: initialHeight.toFixed(3),
      finalHeight: finalHeight.toFixed(3),
      heightReductionRatio,
      minCV: minCVNum.toFixed(3),
      maxCV: maxCVNum.toFixed(3),
      cvName: hillsData.cvNames[0] || "CV1",
      isWT: hillsData.effectiveBiasFactor > 1
    };
  }, [hillsData]);

  // Export calculated FES as PLUMED compatible fes.dat
  const handleExportFES = () => {
    if (!currentFrameData) return;
    const header = [
      `#! FIELDS ${hillsData.cvNames[0] || "CV1"} file.free ${hillsData.cvNames[0] || "CV1"}_der`,
      `#! SET min_${hillsData.cvNames[0] || "CV1"} ${currentFrameData.gridPoints[0].s}`,
      `#! SET max_${hillsData.cvNames[0] || "CV1"} ${currentFrameData.gridPoints[currentFrameData.gridPoints.length - 1].s}`,
      `#! SET nbins_${hillsData.cvNames[0] || "CV1"} ${numBins}`,
      `#! SET periodic_${hillsData.cvNames[0] || "CV1"} false`,
      `#! Reconstructed with MetadynWeb HILLS Visualizer`,
      `#! BiasFactor: ${hillsData.effectiveBiasFactor}`,
      `#! Energy Unit: ${energyUnits}`
    ].join("\n");

    const lines = currentFrameData.gridPoints.map((p) => `  ${p.s}   ${p.fes}   0.0000`);
    const content = header + "\n" + lines.join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `fes_${hillsData.cvNames[0] || "CV1"}_reconstructed.dat`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="flex flex-col w-full max-w-7xl mx-auto space-y-6 relative min-h-[75vh]"
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
                Instant reading and non-blocking background Web Worker processing
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Non-blocking background Web Worker Loading Spinner & Progress Bar */}
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
                60 FPS Real-Time Engine
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-1">
              Exact F(s) = -V(s) reconstruction summing 100% of gaussian hills without resolution loss
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

      {/* Error notification banner if parsing fails */}
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
            <h2 className="text-xl font-extrabold text-white">HILLS File Visualizer (PLUMED)</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Drag your <code className="text-cyan-300 bg-slate-950 px-1.5 py-0.5 rounded font-mono">HILLS</code> file directly onto this window or click the button below to select it from your computer.
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
            <span className="text-[10px] text-slate-500 mt-0.5">Total deposits</span>
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
              <Activity size={13} className="text-emerald-400" /> Collective Variable
            </span>
            <span className="text-lg font-bold text-emerald-300 mt-1 font-mono truncate">
              {stats.cvName}
            </span>
            <span className="text-[10px] text-slate-500 mt-0.5 font-mono">
              [{stats.minCV}, {stats.maxCV}]
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

            <button
              onClick={() => setActiveTab("convergence")}
              className={`px-4 py-2 rounded-lg font-bold transition-all flex items-center gap-2 ${
                activeTab === "convergence"
                  ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Clock size={15} /> Time Convergence
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
                  Reconstructed Free Energy Profile F(s)
                </h2>
                <p className="text-slate-400 text-xs">
                  Free Energy Surface reconstruction from sum of gaussian HILLS
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleExportFES}
                  className="px-3 py-1.5 bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/60 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
                  title="Export PLUMED-compatible fes.dat file"
                >
                  <Download size={14} /> Export fes.dat
                </button>
              </div>
            </div>

            {/* Recharts 1D FES Line Plot (Instant 60 FPS Real-Time Animation) */}
            <div className="h-80 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={currentFrameData.gridPoints}
                  margin={{ top: 15, right: 25, left: 10, bottom: 20 }}
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
                    domain={isZeroRefMode ? [0, 'auto'] : ['auto', 'auto']}
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
                </AreaChart>
              </ResponsiveContainer>
            </div>

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

              <div className="space-y-2.5 text-xs">
                <label className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all">
                  <span className="font-semibold text-slate-200">
                    Direct Absolute Potential [F(s) = -V(s)]
                  </span>
                  <input
                    type="radio"
                    name="zeroRef"
                    checked={!isZeroRefMode}
                    onChange={() => setIsZeroRefMode(false)}
                    className="accent-indigo-500"
                  />
                </label>

                <label className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 cursor-pointer hover:border-slate-700 transition-all">
                  <span className="font-semibold text-slate-200">
                    Relative Potential (Minimum = 0)
                  </span>
                  <input
                    type="radio"
                    name="zeroRef"
                    checked={isZeroRefMode}
                    onChange={() => setIsZeroRefMode(true)}
                    className="accent-indigo-500"
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
                  <label className="block text-[10px] text-slate-400 mb-1">Min CV Bound:</label>
                  <input
                    type="text"
                    placeholder="Auto"
                    value={inputGridMin}
                    onChange={(e) => setInputGridMin(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-slate-400 mb-1">Max CV Bound:</label>
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
              Collective Variable Trajectory s(t) Over Time
            </h2>
            <p className="text-slate-400 text-xs">
              Shows system diffusion along the reaction coordinate and barrier crossing events.
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
                  label={{ value: `CV (${hillsData.cvNames[0] || "CV1"})`, angle: -90, position: "insideLeft", offset: 10, fill: "#cbd5e1", fontSize: 12 }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-950 border border-slate-800 p-2.5 rounded-xl shadow-xl text-xs space-y-1">
                          <div className="text-emerald-400 font-mono font-bold">t = {d.time} ps</div>
                          <div className="text-white font-semibold">CV: {d.cv}</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cv"
                  name="Collective Variable"
                  stroke="#34d399"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* TAB 4: Multi-stage Convergence Overlay */}
      {hillsData && activeTab === "convergence" && convergenceData.chartRows && (
        <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
          <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Clock size={18} className="text-cyan-400" />
                FES Convergence Overlay (25%, 50%, 75%, 100%)
              </h2>
              <p className="text-slate-400 text-xs">
                If late-stage profiles overlap almost identically, the free energy profile has converged.
              </p>
            </div>
          </div>

          <div className="h-96 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={convergenceData.chartRows} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="s"
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  label={{ value: `Collective Variable (${hillsData.cvNames[0] || "CV1"})`, position: "insideBottom", offset: -12, fill: "#cbd5e1", fontSize: 12 }}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  label={{ value: `F(s) [${energyUnits}]`, angle: -90, position: "insideLeft", offset: 10, fill: "#cbd5e1", fontSize: 12 }}
                />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />

                <Line type="monotone" dataKey="FES_25%" name="25% Time" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="FES_50%" name="50% Time" stroke="#38bdf8" strokeWidth={1.5} strokeDasharray="2 2" dot={false} />
                <Line type="monotone" dataKey="FES_75%" name="75% Time" stroke="#a855f7" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="FES_100%" name="100% Full" stroke="#f87171" strokeWidth={3} dot={false} />
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
