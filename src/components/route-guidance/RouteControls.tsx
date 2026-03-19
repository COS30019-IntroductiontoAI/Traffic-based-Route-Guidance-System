import { motion } from "framer-motion";
import { Clock, Route, ArrowRight, CheckCircle2, Crosshair } from "lucide-react";

interface RouteControlsProps {
  origin: string;
  destination: string;
  topK: number;
  onOriginChange: (v: string) => void;
  onDestinationChange: (v: string) => void;
  onTopKChange: (v: number) => void;
  onFindRoutes: () => void;
  onSelectOrigin: () => void;
  onSelectDestination: () => void;
  selectingFor: "origin" | "destination" | null;
  routes: { nodes: string[]; time: number; distance: number }[];
  selectedRoute: number;
  onSelectRoute: (i: number) => void;
}

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

export function RouteControls({
  origin, destination, topK,
  onOriginChange, onDestinationChange, onTopKChange,
  onFindRoutes, onSelectOrigin, onSelectDestination, selectingFor,
  routes, selectedRoute, onSelectRoute,
}: RouteControlsProps) {
  return (
    <motion.div variants={item} className="space-y-4">
      <div className="bg-white rounded-[24px] p-6 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] border border-slate-100 space-y-6">
        <div className="flex items-stretch gap-4">
          <div className="flex flex-col items-center py-3">
            <div className="w-3.5 h-3.5 rounded-full bg-blue-600 relative z-10" />
            <div className="w-0.5 flex-1 bg-slate-200 -my-1" />
            <div className="w-3.5 h-3.5 rounded-full bg-purple-500 relative z-10" />
          </div>
          <div className="flex-1 space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1.5 block">Origin (SCATS Node)</label>
              <div className="flex gap-2 items-center">
                <input
                  type="text" value={origin}
                  onChange={(e) => onOriginChange(e.target.value)}
                  className="flex-1 h-11 px-3.5 rounded-xl bg-slate-50 text-sm font-medium text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  onClick={onSelectOrigin}
                  className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center transition-all ${
                    selectingFor === "origin" 
                      ? "bg-blue-100 text-blue-600 ring-2 ring-blue-500/20" 
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1.5 block">Destination (SCATS Node)</label>
              <div className="flex gap-2 items-center">
                <input
                  type="text" value={destination}
                  onChange={(e) => onDestinationChange(e.target.value)}
                  className="flex-1 h-11 px-3.5 rounded-xl bg-slate-50 text-sm font-medium text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  onClick={onSelectDestination}
                  className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center transition-all ${
                    selectingFor === "destination" 
                      ? "bg-blue-100 text-blue-600 ring-2 ring-blue-500/20" 
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-medium text-slate-600">Top-K Routes</span>
            <span className="text-sm font-bold text-slate-800">{topK}</span>
          </div>
          <input
            type="range" min={1} max={5} value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <button 
          onClick={onFindRoutes} 
          className="w-full h-12 rounded-[14px] bg-blue-600 text-white font-medium text-[15px] transition-colors hover:bg-blue-700 shadow-[0_4px_14px_0_rgba(37,99,235,0.39)]"
        >
          Find Routes
        </button>
      </div>

      {/* Route Results */}
      {routes.length > 0 && (
        <div className="space-y-4 pt-2">
          {routes.map((route, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              onClick={() => onSelectRoute(i)}
              className={`bg-white rounded-[24px] p-5 shadow-[0_2px_10px_-4px_rgba(0,0,0,0.05)] cursor-pointer transition-all duration-300 ${
                selectedRoute === i 
                  ? "border border-blue-200 ring-[3px] ring-blue-50" 
                  : "border border-slate-100 hover:border-slate-200 hover:bg-slate-50/50"
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-800 mb-1">
                    {i === 0 ? "Optimal Route" : `Alternative ${i}`}
                  </h3>
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                      <Clock className="w-3.5 h-3.5 text-slate-400" /> {route.time} min
                    </span>
                    <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                      <Route className="w-3.5 h-3.5 text-slate-400" /> {route.distance} km
                    </span>
                  </div>
                </div>
                {i === 0 && (
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span className="text-xs font-bold text-emerald-500">Best</span>
                  </div>
                )}
              </div>
              <div className="flex items-center flex-wrap gap-x-2 gap-y-2.5">
                {route.nodes.map((node, ni) => (
                  <div key={ni} className="flex items-center text-xs font-mono font-medium text-slate-600">
                    <span>{node}</span>
                    {ni < route.nodes.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-slate-300 ml-2" />
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
