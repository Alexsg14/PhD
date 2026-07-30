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
  ShieldCheck,
  Eye,
  EyeOff,
  Users
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
    const gridMin2User = e.data.gridMin2User;
    const gridMax2User = e.data.gridMax2User;

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

    // B. Timestamp drops (block multiwalker - filters minor simulation restarts < 2000 ps)
    const blockStartIndices = [0];
    for (let i = 1; i < rawRows.length; i++) {
      const prevT = rawRows[i - 1][timeIdx] ?? 0;
      const currT = rawRows[i][timeIdx] ?? 0;
      const dropAmt = prevT - currT;
      if (dropAmt > 2000 || (currT < prevT && currT <= t0Val + 5000)) {
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

    const parsedHills = rawRows.map((row, rowIdx) => {
      const timeVal = row[timeIdx] ?? rowIdx * 10;
      const heightVal = row[heightIdx] ?? 1.0;
      const biasfVal = biasfIdx !== -1 && biasfIdx < row.length ? row[biasfIdx] : null;

      const cvVals = cvIndices.map((ci) => row[ci] ?? 0.0);
      const sigmaVals = sigmaIndices.map((si) => row[si] ?? 0.1);

      let wId = 1;
      if (detectedWalkers > 1) {
        if (isBlockStructure) {
          let bIdx = 0;
          for (let b = blockStartIndices.length - 1; b >= 0; b--) {
            if (rowIdx >= blockStartIndices[b]) {
              bIdx = b;
              break;
            }
          }
          wId = bIdx + 1;
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

      if (gridMinUser !== "" && gridMinUser !== undefined && !isNaN(parseFloat(gridMinUser))) gridMin1 = parseFloat(gridMinUser);
      if (gridMaxUser !== "" && gridMaxUser !== undefined && !isNaN(parseFloat(gridMaxUser))) gridMax1 = parseFloat(gridMaxUser);
      if (gridMin2User !== "" && gridMin2User !== undefined && !isNaN(parseFloat(gridMin2User))) gridMin2 = parseFloat(gridMin2User);
      if (gridMax2User !== "" && gridMax2User !== undefined && !isNaN(parseFloat(gridMax2User))) gridMax2 = parseFloat(gridMax2User);

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

    // Pass parsedHills (or max 20,000 per walker for multiwalker) so trajectory lines stay 100% intact
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
  colorPalette,
  onSelect2DROI,
  onResetZoom
}) {
  const canvasRef = useRef(null);
  const [hoverInfo, setHoverInfo] = useState(null);
  const [showTrajectory, setShowTrajectory] = useState(false);
  const [useAutoCmapColor, setUseAutoCmapColor] = useState(true);
  const [customTrajectoryColor, setCustomTrajectoryColor] = useState("#00b3ff");
  const [projMode, setProjMode] = useState("int"); // "int" (Boltzmann kBT) or "min" (Minimum energy path)

  // Interactive 2D ROI Mouse Selection State
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragCurrent, setDragCurrent] = useState(null);

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
      ctx.fillText(`F(${cvNames[0] || "CV1"}) 1D Projection [${projMode === "int" ? "k_B T Int" : "Min Path"}]`, padLeft + 6, topY1 + 12);

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
    if (!isDragging && hoverInfo && hoverInfo.canvasX >= padLeft && hoverInfo.canvasX <= padLeft + plotW &&
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

    // --- 7. INTERACTIVE MOUSE DRAG SELECTION BOX (2D ROI ZOOM) ---
    if (isDragging && dragStart && dragCurrent) {
      const x1 = Math.min(dragStart.x, dragCurrent.x);
      const x2 = Math.max(dragStart.x, dragCurrent.x);
      const y1 = Math.min(dragStart.y, dragCurrent.y);
      const y2 = Math.max(dragStart.y, dragCurrent.y);

      ctx.fillStyle = "rgba(56, 189, 248, 0.28)";
      ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
      ctx.strokeStyle = "#38bdf8";
      ctx.lineWidth = 1.8;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      ctx.setLineDash([]);
    }
  }, [frameData, energyRefMode, energyUnits, cvNames, hills, colorPalette, showTrajectory, useAutoCmapColor, customTrajectoryColor, projMode, hoverInfo, isDragging, dragStart, dragCurrent]);

  const handleMouseDown = (e) => {
    if (!canvasRef.current || !frameData) return;
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

    if (x >= padLeft && x <= padLeft + plotW && y >= padTop && y <= padTop + plotH) {
      setIsDragging(true);
      setDragStart({ x, y });
      setDragCurrent({ x, y });
    }
  };

  const handleMouseMove = (e) => {
    if (!canvasRef.current || !frameData || !frameData.grid2DFlat) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;

    const rawX = (e.clientX - rect.left) * scaleX;
    const rawY = (e.clientY - rect.top) * scaleY;

    const padLeft = 60;
    const padRight = 145;
    const padTop = 90;
    const padBottom = 58;
    const width = canvasRef.current.width;
    const height = canvasRef.current.height;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const x = Math.min(padLeft + plotW, Math.max(padLeft, rawX));
    const y = Math.min(padTop + plotH, Math.max(padTop, rawY));

    if (isDragging) {
      setDragCurrent({ x, y });
    }

    if (rawX < padLeft || rawX > padLeft + plotW || rawY < padTop || rawY > padTop + plotH) {
      setHoverInfo(null);
      return;
    }

    const { numBinsX, numBinsY, gridMin1, gridMax1, gridMin2, gridMax2, grid2DFlat, projCV1, projCV2 } = frameData;

    const normX = (rawX - padLeft) / plotW;
    const normY = (padTop + plotH - rawY) / plotH;

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
      canvasX: rawX,
      canvasY: rawY,
      cv1: cv1Val.toFixed(3),
      cv2: cv2Val.toFixed(3),
      fes: fesVal,
      proj1: proj1Val,
      proj2: proj2Val
    });
  };

  const handleMouseUp = () => {
    if (isDragging && dragStart && dragCurrent && onSelect2DROI && frameData) {
      const dx = Math.abs(dragCurrent.x - dragStart.x);
      const dy = Math.abs(dragCurrent.y - dragStart.y);
      if (dx > 6 && dy > 6) {
        const padLeft = 60;
        const padRight = 145;
        const padTop = 90;
        const padBottom = 58;
        const width = canvasRef.current.width;
        const height = canvasRef.current.height;
        const plotW = width - padLeft - padRight;
        const plotH = height - padTop - padBottom;

        const x1 = Math.min(dragStart.x, dragCurrent.x);
        const x2 = Math.max(dragStart.x, dragCurrent.x);
        const y1 = Math.min(dragStart.y, dragCurrent.y);
        const y2 = Math.max(dragStart.y, dragCurrent.y);

        const { gridMin1, gridMax1, gridMin2, gridMax2 } = frameData;

        const normX1 = (x1 - padLeft) / plotW;
        const normX2 = (x2 - padLeft) / plotW;

        const normY_bottom = (padTop + plotH - y2) / plotH;
        const normY_top = (padTop + plotH - y1) / plotH;

        const cv1Min = (gridMin1 + normX1 * (gridMax1 - gridMin1)).toFixed(3);
        const cv1Max = (gridMin1 + normX2 * (gridMax1 - gridMin1)).toFixed(3);
        const cv2Min = (gridMin2 + normY_bottom * (gridMax2 - gridMin2)).toFixed(3);
        const cv2Max = (gridMin2 + normY_top * (gridMax2 - gridMin2)).toFixed(3);

        onSelect2DROI(cv1Min, cv1Max, cv2Min, cv2Max);
      }
    }
    setIsDragging(false);
    setDragStart(null);
    setDragCurrent(null);
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
            <div className="flex items-center gap-2 bg-slate-950/80 px-2.5 py-1 rounded-xl border border-slate-800 text-xs">
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-400">
                <input
                  type="checkbox"
                  checked={useAutoCmapColor}
                  onChange={(e) => setUseAutoCmapColor(e.target.checked)}
                  className="accent-indigo-500 rounded"
                />
                <span>Auto-Contrast Color</span>
              </label>

              {!useAutoCmapColor && (
                <div className="flex items-center gap-1 border-l border-slate-800 pl-2">
                  <span className="text-[10px] text-slate-400">Color:</span>
                  <input
                    type="color"
                    value={customTrajectoryColor}
                    onChange={(e) => setCustomTrajectoryColor(e.target.value)}
                    className="w-5 h-5 bg-transparent border-0 cursor-pointer rounded overflow-hidden"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* 1D Projection Mode Toggle */}
          <div className="flex items-center bg-slate-950/80 p-0.5 rounded-xl border border-slate-800 text-[11px]">
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
                ? "bg-cyan-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
                }`}
              title="Minimum energy path: F_min(s₁) = min_s₂ F(s₁, s₂)"
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

          {onResetZoom && (
            <button
              onClick={onResetZoom}
              className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/60 rounded-xl text-[11px] font-semibold flex items-center gap-1 transition-all shadow-sm"
              title="Reset Zoom / Clear 2D ROI (Double-click canvas to reset)"
            >
              <RotateCcw size={12} className="text-amber-400" /> Reset Zoom
            </button>
          )}
        </div>

        {hoverInfo ? (
          <div className="flex items-center gap-3 font-mono text-xs bg-slate-950/90 px-3 py-1 rounded-xl border border-indigo-500/40 shadow-lg">
            <span className="text-slate-300">{cvNames[0] || "CV1"}: <strong className="text-cyan-300">{hoverInfo.cv1}</strong> {hoverInfo.proj1 !== null && <span className="text-cyan-400 text-[10px]">(F₁: {hoverInfo.proj1})</span>}</span>
            <span className="text-slate-300">{cvNames[1] || "CV2"}: <strong className="text-purple-300">{hoverInfo.cv2}</strong> {hoverInfo.proj2 !== null && <span className="text-purple-400 text-[10px]">(F₂: {hoverInfo.proj2})</span>}</span>
            <span className="text-rose-400 font-bold">F 2D: {hoverInfo.fes} {energyUnits}</span>
          </div>
        ) : (
          <span className="text-[11px] text-slate-400 font-mono italic">Click & drag box to zoom (ROI) • Double-click canvas or click Reset Zoom to revert</span>
        )}
      </div>

      <div className="relative border border-slate-800 rounded-2xl overflow-hidden shadow-2xl bg-slate-950 p-1.5 w-full flex justify-center select-none">
        <canvas
          ref={canvasRef}
          width={860}
          height={480}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onDoubleClick={onResetZoom}
          onMouseLeave={() => {
            if (isDragging) handleMouseUp();
            setHoverInfo(null);
          }}
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
  inputGridMin2,
  setInputGridMin2,
  inputGridMax2,
  setInputGridMax2,
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
                <label className="block text-[9px] text-cyan-400 mb-0.5 font-medium">Min CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMin}
                  onChange={(e) => setInputGridMin && setInputGridMin(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
              <div>
                <label className="block text-[9px] text-cyan-400 mb-0.5 font-medium">Max CV1:</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={inputGridMax}
                  onChange={(e) => setInputGridMax && setInputGridMax(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                />
              </div>
            </div>

            {hillsMetadata?.is2D && (
              <div className="grid grid-cols-2 gap-2 pt-0.5">
                <div>
                  <label className="block text-[9px] text-purple-400 mb-0.5 font-medium">Min CV2:</label>
                  <input
                    type="text"
                    placeholder="Auto"
                    value={inputGridMin2 || ""}
                    onChange={(e) => setInputGridMin2 && setInputGridMin2(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-purple-300 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[9px] text-purple-400 mb-0.5 font-medium">Max CV2:</label>
                  <input
                    type="text"
                    placeholder="Auto"
                    value={inputGridMax2 || ""}
                    onChange={(e) => setInputGridMax2 && setInputGridMax2(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-purple-300 font-mono"
                  />
                </div>
              </div>
            )}
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
  gridMin2User = "",
  gridMax2User = "",
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
  inputGridMin2 = "",
  setInputGridMin2,
  inputGridMax2 = "",
  setInputGridMax2,
  handleApplyGridParams: propApplyGridParams,
  handleResetGridBounds: propResetGridBounds,
  hillsMetadata,
  setGridMinUser,
  setGridMaxUser,
  setGridMin2User,
  setGridMax2User,
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

  // Fallback state if props are not provided
  const [internalMin2User, setInternalMin2User] = useState("");
  const [internalMax2User, setInternalMax2User] = useState("");
  const [internalInputMin2, setInternalInputMin2] = useState("");
  const [internalInputMax2, setInternalInputMax2] = useState("");

  const activeGridMin2User = gridMin2User !== undefined ? gridMin2User : internalMin2User;
  const activeGridMax2User = gridMax2User !== undefined ? gridMax2User : internalMax2User;
  const activeInputGridMin2 = inputGridMin2 !== undefined ? inputGridMin2 : internalInputMin2;
  const activeInputGridMax2 = inputGridMax2 !== undefined ? inputGridMax2 : internalInputMax2;

  const actualSetGridMin2User = setGridMin2User || setInternalMin2User;
  const actualSetGridMax2User = setGridMax2User || setInternalMax2User;
  const actualSetInputGridMin2 = setInputGridMin2 || setInternalInputMin2;
  const actualSetInputGridMax2 = setInputGridMax2 || setInternalInputMax2;

  // Interactive Mouse Box Zoom State (1D)
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
    actualSetInputGridMin2("");
    actualSetInputGridMax2("");
    actualSetGridMin2User("");
    actualSetGridMax2User("");
  });
  const handleApplyGridParams = propApplyGridParams || ((e) => e?.preventDefault());

  const handleSelect2DROI = (min1, max1, min2, max2) => {
    if (setGridMinUser) setGridMinUser(min1);
    if (setGridMaxUser) setGridMaxUser(max1);
    if (setInputGridMin) setInputGridMin(min1);
    if (setInputGridMax) setInputGridMax(max1);

    actualSetGridMin2User(min2);
    actualSetGridMax2User(max2);
    actualSetInputGridMin2(min2);
    actualSetInputGridMax2(max2);
  };

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
      gridMaxUser,
      gridMin2User: activeGridMin2User,
      gridMax2User: activeGridMax2User
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
  }, [numBins, isWtScaling, customBiasFactor, gridMinUser, gridMaxUser, activeGridMin2User, activeGridMax2User]);

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
      <header className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-xl flex justify-between items-center flex-wrap gap-3">
        <div className="flex items-center gap-3 z-10">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
            <BarChart2 size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-sm text-white tracking-wide">
                PLUMED HILLS Visualizer &amp; Inspector
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-950 text-indigo-400 border border-indigo-800/60 rounded-full">
                {hillsData?.is2D ? "2D Mode Enabled" : "1D / 2D Engine"}
              </span>
            </div>
            <p className="text-xs text-indigo-400 font-mono font-medium">
              Reconstruction of 1D and 2D Free Energy Surfaces from PLUMED HILLS data
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 z-10">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current.click()}
            disabled={isLoading}
            className="py-2 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
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
              inputGridMin2={activeInputGridMin2}
              setInputGridMin2={actualSetInputGridMin2}
              inputGridMax2={activeInputGridMax2}
              setInputGridMax2={actualSetInputGridMax2}
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
                      ? "Click and drag a box across the 2D heatmap to select a 2D zoom region (ROI)"
                      : "Click and drag across the chart to select a vertical zoom region (ROI) for export"}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {(gridMinUser || gridMaxUser || activeGridMin2User || activeGridMax2User) && (
                    <div className="flex items-center gap-2 bg-cyan-950/90 border border-cyan-600/70 px-3 py-1 rounded-xl text-xs text-cyan-300 font-mono shadow-sm">
                      <ZoomIn size={14} className="text-cyan-400 animate-pulse" />
                      <span>
                        {hillsData.is2D
                          ? `ROI CV1: [${gridMinUser || "Min"}, ${gridMaxUser || "Max"}] • CV2: [${activeGridMin2User || "Min"}, ${activeGridMax2User || "Max"}]`
                          : `ROI: [${gridMinUser || "Min"}, ${gridMaxUser || "Max"}]`}
                      </span>
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
                  onSelect2DROI={handleSelect2DROI}
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

          {/* TAB 3: Collective Variable Trajectory s(t) & Multi-Walker Matrix Grid Subplots */}
          {hillsData && activeTab === "cv" && (
            <div className="bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4 w-full">
              <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-3">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Activity size={18} className="text-emerald-400" />
                    {hillsData.is2D ? "Collective Variables Trajectory (CV1, CV2) Over Time" : "Collective Variable Trajectory s(t) Over Time"}
                  </h2>
                  <p className="text-slate-400 text-xs mt-0.5">
                    Shows system diffusion along reaction coordinate(s). Multi-walker HILLS are rendered in subplots.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* CV Toggles */}
                  <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800 text-xs">
                    <button
                      onClick={() => setShowCV1(!showCV1)}
                      className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1.5 transition-all text-xs ${showCV1
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
                        className={`px-2.5 py-1 rounded-lg font-bold flex items-center gap-1.5 transition-all text-xs ${showCV2
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
              <div className={`grid gap-4 w-full ${walkerParsedData.numWalkers === 16
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
                        <span className="px-2 py-0.5 bg-indigo-950 text-indigo-300 border border-indigo-700/60 rounded-lg font-bold font-mono text-[12px]">
                          W {wObj.walkerId}
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
