import React, { useState } from "react";
import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";
import MetadynamicsLab2D from "./MetadynamicsLab2D";
import { Activity, Layers } from "lucide-react";

function App() {
  const [simDimension, setSimDimension] = useState("1D"); // "1D" | "2D"

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6 px-4 sm:px-6 lg:px-8 selection:bg-cyan-500 selection:text-white relative overflow-x-hidden">
      {/* Background Ambient Glow Effects */}
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Top Global Dimension Switcher Bar */}
      <div className="max-w-7xl mx-auto mb-5 flex justify-between items-center bg-slate-900/90 backdrop-blur-md p-2 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-2 pl-3">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Metadynamics Dimension Mode:
          </span>
        </div>
        
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setSimDimension("1D")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              simDimension === "1D"
                ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity size={15} /> 1D Simulator (CV_x)
          </button>
          
          <button
            onClick={() => setSimDimension("2D")}
            className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
              simDimension === "2D"
                ? "bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/20"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers size={15} /> 2D Simulator (CV_x, CV_y)
          </button>
        </div>
      </div>

      {simDimension === "1D" ? <MetadynamicsLab /> : <MetadynamicsLab2D />}
    </div>
  );
}

export default App;
