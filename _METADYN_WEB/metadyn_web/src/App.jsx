import "./index.css";
import MetadynamicsLab from "./MetadynamicsLab";

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6 px-4 sm:px-6 lg:px-8 selection:bg-cyan-500 selection:text-white relative overflow-x-hidden">
      {/* Background Ambient Glow Effects */}
      <div className="fixed -top-40 -left-40 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed top-1/3 -right-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="fixed -bottom-40 left-1/3 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      
      <MetadynamicsLab />
    </div>
  );
}

export default App;
