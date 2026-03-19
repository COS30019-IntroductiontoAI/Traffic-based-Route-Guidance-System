import { motion } from "framer-motion";
import { useState, useMemo, useCallback } from "react";
import { CityMap } from "@/components/route-guidance/CityMap";
import { RouteControls } from "@/components/route-guidance/RouteControls";
import { cityNodes, cityEdges, findShortestPaths } from "@/components/route-guidance/cityMapData";
import { MapPin } from "lucide-react";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, y: 15 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] as const } },
};

export default function RouteGuidance() {
  const [origin, setOrigin] = useState("4000");
  const [destination, setDestination] = useState("4609");
  const [topK, setTopK] = useState(3);
  const [selectedRoute, setSelectedRoute] = useState(0);
  const [selectingFor, setSelectingFor] = useState<"origin" | "destination" | null>(null);

  const routes = useMemo(
    () => findShortestPaths(cityNodes, cityEdges, origin, destination, topK),
    [origin, destination, topK]
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
    <motion.div variants={container} initial="hidden" animate="show" className="p-8 max-w-[1600px] mx-auto w-full">
      <motion.div variants={item} className="mb-8">
        <h1 className="text-[28px] font-bold text-slate-800 tracking-tight mb-2">
          Route Guidance
        </h1>
        <p className="text-[15px] font-medium text-slate-500 max-w-2xl">
          Find optimal travel routes across the city network — click nodes on the map or type SCATS IDs.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls */}
        <div className="lg:col-span-4 xl:col-span-4">
          <RouteControls
            origin={origin}
            destination={destination}
            topK={topK}
            onOriginChange={setOrigin}
            onDestinationChange={setDestination}
            onTopKChange={setTopK}
            onFindRoutes={() => setSelectedRoute(0)}
            onSelectOrigin={() => setSelectingFor(selectingFor === "origin" ? null : "origin")}
            onSelectDestination={() => setSelectingFor(selectingFor === "destination" ? null : "destination")}
            selectingFor={selectingFor}
            routes={routes}
            selectedRoute={selectedRoute}
            onSelectRoute={setSelectedRoute}
          />
        </div>

        {/* Map */}
        <motion.div variants={item} className="lg:col-span-8 xl:col-span-8">
          <div className="bg-white h-[760px] relative overflow-hidden rounded-[32px] border border-slate-100 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.06)] ring-1 ring-slate-100">
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
            <div className="absolute bottom-6 left-6 flex flex-col gap-3">
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-full bg-blue-600 shadow-sm" />
                <span className="text-sm font-medium text-slate-600">Origin</span>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="w-4 h-4 rounded-full bg-purple-500 shadow-sm" />
                <span className="text-sm font-medium text-slate-600">Destination</span>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-1 rounded-full bg-blue-600 shadow-sm" />
                <span className="text-sm font-medium text-slate-600">Route</span>
              </div>
            </div>

            {/* Node count */}
            <div className="absolute top-6 right-6 flex items-center gap-2 text-slate-500">
              <MapPin className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-bold tracking-wide">{cityNodes.length} nodes</span>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}