import React, { useState } from "react";
import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";
import MetadynamicsLab2D from "./MetadynamicsLab2D";
import HillsVisualizer from "./HillsVisualizer";
import { Activity, Layers, BarChart2, ShieldCheck } from "lucide-react";

function App() {
  const [simDimension, setSimDimension] = useState("1D"); // "1D" | "2D" | "HILLS"

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6 px-4 sm:px-6 lg:px-8 selection:bg-cyan-500 selection:text-white relative overflow-x-hidden">
      {/* Background Ambient Glow Effects */}
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Outer Layout: Floating Left Navigation Card + Main Content Area */}
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-start gap-6">
        
        {/* Floating Left Navigation Card */}
        <aside className="w-full lg:w-64 bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-4 shadow-2xl shrink-0 space-y-4">
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

          {/* Footer Info inside floating card */}
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
            <HillsVisualizer />
          )}
        </main>

      </div>
    </div>
  );
}

export default App;
