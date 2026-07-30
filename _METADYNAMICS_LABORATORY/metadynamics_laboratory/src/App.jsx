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
