import React, { useState } from "react";
import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";
import MetadynamicsLab2D from "./MetadynamicsLab2D";
import HillsVisualizer from "./HillsVisualizer";
import {
  Activity,
  Layers,
  BarChart2,
  ShieldCheck,
  Sliders,
  RefreshCw,
  RotateCcw
} from "lucide-react";

function App() {
  const [simDimension, setSimDimension] = useState("HILLS"); // "1D" | "2D" | "HILLS"

  // Shared state for HILLS visualizer configuration
  const [numBins, setNumBins] = useState(300);
  const [customBiasFactor, setCustomBiasFactor] = useState("");
  const [gridMinUser, setGridMinUser] = useState("");
  const [gridMaxUser, setGridMaxUser] = useState("");

  const [inputNumBins, setInputNumBins] = useState("300");
  const [inputCustomBias, setInputCustomBias] = useState("");
  const [inputGridMin, setInputGridMin] = useState("");
  const [inputGridMax, setInputGridMax] = useState("");

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
  };

  const handleResetGridBounds = () => {
    setInputGridMin("");
    setInputGridMax("");
    setGridMinUser("");
    setGridMaxUser("");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6 px-4 sm:px-6 lg:px-8 selection:bg-cyan-500 selection:text-white relative overflow-x-hidden">
      {/* Background Ambient Glow Effects */}
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Outer Full-Width Responsive Layout */}
      <div className="w-full max-w-[1920px] mx-auto flex flex-col lg:flex-row items-start gap-6">
        
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
          <div className="space-y-2">
            <div className="px-1 mb-1.5 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Navigation Mode
              </span>
            </div>

            <button
              onClick={() => setSimDimension("1D")}
              className={`w-full p-3 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                simDimension === "1D"
                  ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 border border-cyan-400/30"
                  : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
              }`}
            >
              <Activity size={18} className={simDimension === "1D" ? "text-white" : "text-cyan-400"} />
              <div>
                <div>1D Simulator</div>
                <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">1 Collective Variable</div>
              </div>
            </button>

            <button
              onClick={() => setSimDimension("2D")}
              className={`w-full p-3 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                simDimension === "2D"
                  ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/25 border border-purple-400/30"
                  : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
              }`}
            >
              <Layers size={18} className={simDimension === "2D" ? "text-white" : "text-purple-400"} />
              <div>
                <div>2D Simulator</div>
                <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">2 Collective Variables</div>
              </div>
            </button>

            <button
              onClick={() => setSimDimension("HILLS")}
              className={`w-full p-3 rounded-xl text-xs font-bold transition-all flex items-center gap-3 text-left ${
                simDimension === "HILLS"
                  ? "bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/25 border border-emerald-400/30"
                  : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-950 border border-slate-800/80"
              }`}
            >
              <BarChart2 size={18} className={simDimension === "HILLS" ? "text-white" : "text-emerald-400"} />
              <div>
                <div>HILLS Inspector</div>
                <div className="text-[10px] font-normal opacity-75 font-mono mt-0.5">PLUMED 1D & 2D</div>
              </div>
            </button>
          </div>

          {/* HILLS Inspector Controls (Rendered when HILLS tab is active) */}
          {simDimension === "HILLS" && (
            <>
              {/* Display Mode Switcher Card */}
              <div className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 space-y-3">
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
                      name="energyRef"
                      checked={energyRefMode === "plateauZero"}
                      onChange={() => setEnergyRefMode("plateauZero")}
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
                      name="energyRef"
                      checked={energyRefMode === "minZero"}
                      onChange={() => setEnergyRefMode("minZero")}
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
                      name="energyRef"
                      checked={energyRefMode === "raw"}
                      onChange={() => setEnergyRefMode("raw")}
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
                      onChange={(e) => setIsWtScaling(e.target.checked)}
                      className="accent-indigo-500 rounded"
                    />
                  </label>
                </div>
              </div>

              {/* Grid & Calculation Settings Form */}
              <form onSubmit={handleApplyGridParams} className="bg-slate-950/80 border border-slate-800/90 rounded-xl p-4 space-y-3">
                <h3 className="font-bold text-[11px] uppercase tracking-wider text-slate-300 flex items-center gap-2 border-b border-slate-800/80 pb-2">
                  <Sliders size={14} className="text-indigo-400" />
                  FES Grid Parameters
                </h3>

                {!hillsMetadata?.is2D && (
                  <div>
                    <label className="block text-[11px] text-slate-400 mb-1 font-medium">
                      Grid Resolution (Bins):
                    </label>
                    <input
                      type="number"
                      min="50"
                      max="1000"
                      value={inputNumBins}
                      onChange={(e) => setInputNumBins(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-cyan-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-[11px] text-slate-400 mb-1 font-medium">
                    Well-Tempered Bias Factor (γ):
                  </label>
                  <input
                    type="text"
                    placeholder={`Detected: ${hillsMetadata?.effectiveBiasFactor ?? 60}`}
                    value={inputCustomBias}
                    onChange={(e) => setInputCustomBias(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-indigo-300 font-mono focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-[11px] text-slate-400 mb-1 font-medium">
                    Energy Units:
                  </label>
                  <select
                    value={energyUnits}
                    onChange={(e) => setEnergyUnits(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 outline-none"
                  >
                    <option value="kJ/mol">kJ/mol</option>
                    <option value="kcal/mol">kcal/mol</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div>
                    <label className="block text-[9px] text-slate-400 mb-1">Min CV1 Bound:</label>
                    <input
                      type="text"
                      placeholder="Auto"
                      value={inputGridMin}
                      onChange={(e) => setInputGridMin(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] text-slate-400 mb-1">Max CV1 Bound:</label>
                    <input
                      type="text"
                      placeholder="Auto"
                      value={inputGridMax}
                      onChange={(e) => setInputGridMax(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 font-mono"
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
                    className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 rounded-xl text-xs font-semibold"
                    title="Reset CV Bounds to Auto"
                  >
                    <RotateCcw size={14} />
                  </button>
                </div>

              </form>
            </>
          )}

          {/* Footer Info inside left column sidebar */}
          <div className="pt-3 border-t border-slate-800/80 px-1 text-[10px] text-slate-500 flex items-center justify-between">
            <span className="font-semibold text-slate-400 flex items-center gap-1">
              <ShieldCheck size={12} className="text-cyan-400" /> Lab v1.0
            </span>
            <span className="text-[9px] text-slate-500 font-mono">React 19</span>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 w-full min-w-0">
          {simDimension === "1D" ? (
            <MetadynamicsLab />
          ) : simDimension === "2D" ? (
            <MetadynamicsLab2D />
          ) : (
            <HillsVisualizer
              numBins={numBins}
              customBiasFactor={customBiasFactor}
              gridMinUser={gridMinUser}
              gridMaxUser={gridMaxUser}
              energyUnits={energyUnits}
              energyRefMode={energyRefMode}
              isWtScaling={isWtScaling}
              setGridMinUser={setGridMinUser}
              setGridMaxUser={setGridMaxUser}
              setInputGridMin={setInputGridMin}
              setInputGridMax={setInputGridMax}
              onMetadataLoaded={setHillsMetadata}
            />
          )}
        </main>

      </div>
    </div>
  );
}

export default App;
