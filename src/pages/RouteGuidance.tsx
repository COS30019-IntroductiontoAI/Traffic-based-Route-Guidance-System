import { motion, AnimatePresence } from "framer-motion";
import { useState, useMemo, useCallback } from "react";
import { CityMap } from "@/components/route-guidance/CityMap";
import { RouteControls } from "@/components/route-guidance/RouteControls";
import { RouteDetails } from "@/components/route-guidance/RouteDetails";
import { cityNodes, cityEdges, findShortestPaths } from "@/components/route-guidance/cityMapData";
import { MapPin } from "lucide-react";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

export default function RouteGuidance() {
  const [origin, setOrigin] = useState("4004");
  const [destination, setDestination] = useState("4609");
  const [topK, setTopK] = useState(5);
  const [algorithm, setAlgorithm] = useState("xgboost");
  const [selectedRoute, setSelectedRoute] = useState(0);
  const [selectingFor, setSelectingFor] = useState<"origin" | "destination" | null>(null);
  const [showDetails, setShowDetails] = useState(true);

  const routes = useMemo(
    () => findShortestPaths(cityNodes, cityEdges, origin, destination, topK, algorithm),
    [origin, destination, topK, algorithm]
  );

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      if (selectingFor === "origin") {
        setOrigin(nodeId);
        setSelectingFor(null);
      } else if (selectingFor === "destination") {
        setDestination(nodeId);
        setSelectingFor(null);
      }
    },
    [selectingFor]
  );

  return (
    <div className="p-8 max-w-[1500px] w-full min-h-screen font-sans">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={item}>
          <h1 className="text-[26px] font-bold tracking-tight text-slate-800">
            Route Guidance
          </h1>
          <p className="text-[14px] text-slate-500 font-medium mt-1">
            Find optimal travel routes using ML-predicted traffic — select an algorithm, click nodes or type SCATS IDs.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          {/* Controls */}
          <div className="xl:col-span-4 space-y-4">
            <RouteControls
              origin={origin}
              destination={destination}
              topK={topK}
              algorithm={algorithm}
              onOriginChange={setOrigin}
              onDestinationChange={setDestination}
              onTopKChange={setTopK}
              onAlgorithmChange={setAlgorithm}
              onFindRoutes={() => { setSelectedRoute(0); setShowDetails(true); }}
              onSelectOrigin={() => setSelectingFor(selectingFor === "origin" ? null : "origin")}
              onSelectDestination={() => setSelectingFor(selectingFor === "destination" ? null : "destination")}
              selectingFor={selectingFor}
              routes={routes}
              selectedRoute={selectedRoute}
              onSelectRoute={(i) => { setSelectedRoute(i); setShowDetails(true); }}
            />
          </div>

          {/* Map + Details */}
          <div className="xl:col-span-8 space-y-6">
            <motion.div variants={item}>
              <div className="bg-white rounded-[24px] shadow-sm border border-slate-200/60 h-[580px] relative overflow-hidden p-0">
                <CityMap
                  nodes={cityNodes}
                  edges={cityEdges}
                  routes={routes}
                  selectedRoute={selectedRoute}
                  origin={origin}
                  destination={destination}
                  onNodeClick={handleNodeClick}
                  selectingFor={selectingFor}
                />

                {/* Legend */}
                <div className="absolute bottom-6 left-6 p-4 text-[13px] text-slate-500 font-medium space-y-2.5 pointer-events-none">
                  <div className="flex items-center gap-2.5">
                    <div className="w-3.5 h-3.5 rounded-full bg-blue-500 shadow-sm" />
                    <span>Origin</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-3.5 h-3.5 rounded-full bg-red-500 shadow-sm" />
                    <span>Destination</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="flex gap-0.5">
                      <div className="w-2.5 h-[3px] rounded-full bg-amber-500 shadow-sm" />
                    </div>
                    <span>Selected Route</span>
                  </div>
                </div>

                {/* Node count + algo */}
                <div className="absolute top-6 right-6 text-[13px] text-slate-500 font-bold flex items-center gap-3 pointer-events-none">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{cityNodes.length} nodes</span>
                  </span>
                  <span className="w-[1.5px] h-3.5 bg-slate-300" />
                  <span className="uppercase">{algorithm}</span>
                </div>
              </div>
            </motion.div>

            {/* Route Details */}
            <AnimatePresence>
              {showDetails && routes[selectedRoute] && (
                <RouteDetails
                  route={routes[selectedRoute]}
                  index={selectedRoute}
                  algorithm={algorithm}
                  onClose={() => setShowDetails(false)}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>
    </div>
  );
}