import { motion } from "framer-motion";
import { Clock, Route, ArrowRight, CheckCircle2, Crosshair } from "lucide-react";
import { ROUTE_ALGORITHMS, type AlgorithmId, type DataKey, type RouteResult } from "./cityMapData";
import { TrafficBadge } from "./TrafficBadge";

interface RouteControlsProps {
  origin: string;
  destination: string;
  topK: number;
  algorithm: AlgorithmId;
  onOriginChange: (v: string) => void;
  onDestinationChange: (v: string) => void;
  onTopKChange: (v: number) => void;
  onAlgorithmChange: (v: AlgorithmId) => void;
  year: DataKey;
  onYearChange: (v: DataKey) => void;
  onFindRoutes: () => void;
  onSelectOrigin: () => void;
  onSelectDestination: () => void;
  selectingFor: "origin" | "destination" | null;
  routes: RouteResult[];
  selectedRoute: number;
  onSelectRoute: (i: number) => void;
  isGraphLoading: boolean;
  isRoutesLoading: boolean;
}

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

const TRAFFIC_PRIORITY = {
  clear: 0,
  moderate: 1,
  heavy: 2,
} as const;

function getWorstTrafficLevel(route: RouteResult): "clear" | "moderate" | "heavy" {
  return route.segments.reduce<"clear" | "moderate" | "heavy">((worst, segment) => {
    return TRAFFIC_PRIORITY[segment.traffic] > TRAFFIC_PRIORITY[worst] ? segment.traffic : worst;
  }, "clear");
}

export function RouteControls({
  origin,
  destination,
  topK,
  algorithm,
  year,
  onOriginChange,
  onDestinationChange,
  onTopKChange,
  onAlgorithmChange,
  onYearChange,
  onFindRoutes,
  onSelectOrigin,
  onSelectDestination,
  selectingFor,
  routes,
  selectedRoute,
  onSelectRoute,
  isGraphLoading,
  isRoutesLoading,
}: RouteControlsProps) {
  const isSubmitDisabled = isGraphLoading || isRoutesLoading || !origin || !destination || origin === destination;

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
                  type="text"
                  value={origin}
                  onChange={(e) => onOriginChange(e.target.value)}
                  disabled={isGraphLoading}
                  className="flex-1 h-11 px-4 rounded-xl bg-slate-50 text-sm text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                />
                <button
                  onClick={onSelectOrigin}
                  disabled={isGraphLoading}
                  className={`flex-shrink-0 h-11 w-11 rounded-xl flex items-center justify-center transition-all ${
                    selectingFor === "origin"
                      ? "bg-blue-50 text-blue-600 ring-2 ring-blue-500/20"
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  } disabled:cursor-not-allowed disabled:opacity-60`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div>
              <label className="text-[13px] text-slate-500 mb-1.5 block">Destination (SCATS ID)</label>
              <div className="flex gap-2 items-center">
                <input
                  type="text"
                  value={destination}
                  onChange={(e) => onDestinationChange(e.target.value)}
                  disabled={isGraphLoading}
                  className="flex-1 h-11 px-4 rounded-xl bg-slate-50 text-sm text-slate-800 border-none outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                />
                <button
                  onClick={onSelectDestination}
                  disabled={isGraphLoading}
                  className={`flex-shrink-0 h-11 w-11 rounded-xl flex items-center justify-center transition-all ${
                    selectingFor === "destination"
                      ? "bg-blue-50 text-blue-600 ring-2 ring-blue-500/20"
                      : "bg-white text-slate-400 hover:text-slate-600 border border-slate-200 hover:border-slate-300"
                  } disabled:cursor-not-allowed disabled:opacity-60`}
                >
                  <Crosshair className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-[13px] text-slate-500 flex items-center gap-1.5">ML Algorithm</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {ROUTE_ALGORITHMS.map((algo) => (
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
                <div className="text-[10px] text-slate-400 leading-tight">{algo.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <label className="text-[13px] text-slate-500 flex items-center gap-1.5">Dataset Year</label>
          <div className="flex bg-slate-100 p-1 rounded-xl">
            {(["2006", "2014"] as const).map((itemYear) => (
              <button
                key={itemYear}
                onClick={() => onYearChange(itemYear)}
                className={`flex-1 py-2 text-[13px] font-medium rounded-lg transition-all ${
                  year === itemYear
                    ? "bg-white text-blue-600 shadow-sm ring-1 ring-slate-200/50"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {itemYear}
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
            type="range"
            min={1}
            max={5}
            value={topK}
            onChange={(e) => onTopKChange(Number(e.target.value))}
            className="w-full h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-blue-600"
          />
        </div>

        <button
          onClick={onFindRoutes}
          disabled={isSubmitDisabled}
          className="w-full h-12 rounded-xl text-white font-medium text-sm transition-all shadow-md hover:shadow-lg bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
        >
          {isRoutesLoading ? "Finding Routes..." : "Find Routes"}
        </button>

        {origin === destination && origin && (
          <p className="text-[12px] text-amber-600">Origin and destination must be different SCATS IDs.</p>
        )}
      </div>

      {routes.length > 0 && (
        <div className="space-y-4">
          <div className="text-sm text-slate-500 px-1">
            {routes.length} routes found via {ROUTE_ALGORITHMS.find((item) => item.id === algorithm)?.name ?? algorithm.toUpperCase()}
          </div>
          <div className="space-y-3">
            {routes.map((route, index) => (
              <motion.div
                key={route.rank ?? index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                onClick={() => onSelectRoute(index)}
                className={`bg-white rounded-[24px] p-5 cursor-pointer transition-all duration-300 relative overflow-hidden group border ${
                  selectedRoute === index
                    ? "border-blue-200 ring-4 ring-blue-50 shadow-sm"
                    : "border-slate-200/60 shadow-sm hover:border-slate-300"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className={`text-[15px] font-semibold mb-2 ${selectedRoute === index ? "text-slate-800" : "text-slate-700"}`}>
                      {index === 0 ? "Optimal Route" : `Alternative ${index}`}
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
                    {index === 0 && (
                      <div className="flex items-center gap-1 text-emerald-500">
                        <CheckCircle2 className="w-4 h-4" />
                        <span className="text-[13px] font-semibold">Best</span>
                      </div>
                    )}
                    <TrafficBadge level={getWorstTrafficLevel(route)} />
                  </div>
                </div>
                <div className="flex items-center flex-wrap gap-x-1.5 gap-y-2">
                  {route.nodes.map((node, nodeIndex) => (
                    <div key={`${route.rank ?? index}-${node}-${nodeIndex}`} className="flex items-center text-[11px] font-medium text-slate-500">
                      <span className={selectedRoute === index ? "text-slate-800" : ""}>{node}</span>
                      {nodeIndex < route.nodes.length - 1 && <ArrowRight className="w-3 h-3 text-slate-300 mx-1" />}
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
