import { motion } from "framer-motion";
import { Clock, Route, ArrowRight, CheckCircle2, Crosshair } from "lucide-react";
import type { RouteResult } from "./cityMapData";
import { TrafficBadge } from "./TrafficBadge";

interface RouteControlsProps {
  origin: string;
  destination: string;
  topK: number;
  algorithm: string;
  onOriginChange: (v: string) => void;
  onDestinationChange: (v: string) => void;
  onTopKChange: (v: number) => void;
  onAlgorithmChange: (v: string) => void;
  onFindRoutes: () => void;
  onSelectOrigin: () => void;
  onSelectDestination: () => void;
  selectingFor: "origin" | "destination" | null;
  routes: RouteResult[];
  selectedRoute: number;
  onSelectRoute: (i: number) => void;
}

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

const algorithms = [
  { id: "xgboost", name: "XGBoost", desc: "Gradient boosting ensemble" },
  { id: "gru", name: "GRU", desc: "Gated Recurrent Unit" },
  { id: "lstm", name: "LSTM", desc: "Long Short-Term Memory" },
  { id: "rf", name: "Random Forest", desc: "Ensemble decision trees" }
];

export function RouteControls({
  origin, destination, topK, algorithm,
  onOriginChange, onDestinationChange, onTopKChange, onAlgorithmChange,
  onFindRoutes, onSelectOrigin, onSelectDestination, selectingFor,
  routes, selectedRoute, onSelectRoute,
}: RouteControlsProps) {
  return (
    <motion.div variants={item} className="space-y-6">
      <div className="bg-white rounded-[24px] p-6 border border-slate-200/60 shadow-sm space-y-6">
        <div className="flex items-stretch gap-4">
          <div className="flex flex-col items-center py-4">
            <div className="w-3.5 h-3.5 rounded-full bg-blue-500 relative z-10" />
            <div className="w-px flex-1 bg-slate-200 -my-1" />
            <div className="w-3.5 h-3.5 rounded-full bg-blue-500 relative z-10" />
          </div>
          <div className="flex-1 space-y-4">
            <div>
              <label className="text-[13px] text-slate-500 mb-1.5 block">Origin (SCATS ID)</label>
              <div className="flex gap-2 items-center">
                <input
                  type="text" value={origin}
                  onChange={(e) => onOriginChange(e.target.value)}
                  className="flex-1 h-11 px-4 rounded-xl bg-slate-50 text-sm text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  onClick={onSelectOrigin}
                  className={`flex-shrink-0 h-11 w-11 rounded-xl flex items-center justify-center transition-all ${
                    selectingFor === "origin" 
                      ? "bg-blue-50 text-blue-600 ring-2 ring-blue-500/20" 
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div>
              <label className="text-[13px] text-slate-500 mb-1.5 block">Destination (SCATS ID)</label>
              <div className="flex gap-2 items-center">
                <input
                  type="text" value={destination}
                  onChange={(e) => onDestinationChange(e.target.value)}
                  className="flex-1 h-11 px-4 rounded-xl bg-slate-50 text-sm text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  onClick={onSelectDestination}
                  className={`flex-shrink-0 h-11 w-11 rounded-xl flex items-center justify-center transition-all ${
                    selectingFor === "destination" 
                      ? "bg-blue-50 text-blue-600 ring-2 ring-blue-500/20" 
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div className="space-y-3">
          <label className="text-[13px] text-slate-500 flex items-center gap-1.5">
            ⚙️ ML Algorithm
          </label>
          <div className="grid grid-cols-2 gap-2.5">
            {algorithms.map((algo) => (
              <button
                key={algo.id}
                onClick={() => onAlgorithmChange(algo.id)}
                className={`text-left p-3 rounded-xl border transition-all ${
                  algorithm === algo.id
                    ? "bg-blue-50/50 border-blue-200 ring-1 ring-blue-100"
                    : "bg-white border-slate-100 hover:border-slate-200"
                }`}
              >
                <div className={`text-[13px] font-medium mb-1 ${algorithm === algo.id ? "text-slate-800" : "text-slate-600"}`}>
                  {algo.name}
                </div>
                <div className="text-[10px] text-slate-400 leading-tight">
                  {algo.desc}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-[13px] text-slate-500">Top-K Routes</span>
            <span className="text-sm font-semibold text-slate-800">{topK}</span>
          </div>
          <input
            type="range" min={1} max={5} value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <button 
          onClick={onFindRoutes} 
          className="w-full h-12 rounded-xl text-white font-medium text-sm transition-all shadow-md hover:shadow-lg bg-blue-500"
        >
          Find Routes
        </button>
      </div>

      {/* Route Results */}
      {routes.length > 0 && (
        <div className="space-y-4">
          <div className="text-sm text-slate-500 px-1">
            {routes.length} routes found via {algorithms.find(a => a.id === algorithm)?.name.toUpperCase() || algorithm.toUpperCase()}
          </div>
          <div className="space-y-3">
            {routes.map((route, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                onClick={() => onSelectRoute(i)}
                className={`bg-white rounded-[24px] p-5 cursor-pointer transition-all duration-300 relative overflow-hidden group border ${
                  selectedRoute === i 
                    ? "border-blue-200 ring-4 ring-blue-50 shadow-sm" 
                    : "border-slate-200/60 shadow-sm hover:border-slate-300"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className={`text-[15px] font-semibold mb-2 ${selectedRoute === i ? "text-slate-800" : "text-slate-700"}`}>
                      {i === 0 ? "Optimal Route" : `Alternative ${i}`}
                    </h3>
                    <div className="flex items-center gap-4 text-[13px] text-slate-500">
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-400" /> {route.time} min
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Route className="w-3.5 h-3.5 text-slate-400" /> {route.distance} km
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    {i === 0 && (
                      <div className="flex items-center gap-1 text-emerald-500">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-[13px] font-semibold">Best</span>
                      </div>
                    )}
                    {/* Sum the traffic by finding worst traffic in segments if possible, else moderate string if available */}
                    <TrafficBadge level={route.segments?.[0]?.traffic || "moderate"} />
                  </div>
                </div>
                <div className="flex items-center flex-wrap gap-x-1.5 gap-y-2">
                  {route.nodes.map((node, ni) => (
                    <div key={ni} className="flex items-center text-[11px] font-medium text-slate-500">
                      <span className={selectedRoute === i ? "text-slate-800" : ""}>{node}</span>
                      {ni < route.nodes.length - 1 && (
                        <ArrowRight className="w-3 h-3 text-slate-300 mx-1" />
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
