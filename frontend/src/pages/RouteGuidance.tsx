import { motion, AnimatePresence } from "framer-motion";
import { useState, useCallback, useEffect, useRef } from "react";
import { useApp } from "@/App";
import { CityMap } from "@/components/route-guidance/CityMap";
import { RouteControls } from "@/components/route-guidance/RouteControls";
import { RouteDetails } from "@/components/route-guidance/RouteDetails";
import {
  fetchGraph,
  fetchRouteGuidanceConfig,
  fetchRoutes,
  type AlgorithmId,
  type DataKey,
  type MapEdge,
  type MapNode,
  type RouteGuidanceConfigResponse,
  type RouteGuidanceSelectionOptions,
  type RouteResult,
} from "@/components/route-guidance/cityMapData";
import { LoaderCircle, MapPin, ServerCrash } from "lucide-react";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

const DEFAULT_TOP_K = 5;
const DEFAULT_ALGORITHM: AlgorithmId = "lightgbm";
const DEFAULT_YEAR: DataKey = "2014";
const EMPTY_SELECTION_OPTIONS: RouteGuidanceSelectionOptions = {
  data: DEFAULT_YEAR,
  available_dates: [],
  min_date: null,
  max_date: null,
  times: [],
  default_date: null,
  default_time: null,
};

export default function RouteGuidance() {
  const { toast } = useApp();
  const [nodes, setNodes] = useState<MapNode[]>([]);
  const [edges, setEdges] = useState<MapEdge[]>([]);
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [topK, setTopK] = useState(DEFAULT_TOP_K);
  const [algorithm, setAlgorithm] = useState<AlgorithmId>(DEFAULT_ALGORITHM);
  const [selectedRoute, setSelectedRoute] = useState(0);
  const [selectingFor, setSelectingFor] = useState<"origin" | "destination" | null>(null);
  const [showDetails, setShowDetails] = useState(true);
  const [year, setYear] = useState<DataKey>(DEFAULT_YEAR);
  const [routes, setRoutes] = useState<RouteResult[]>([]);
  const [forecastTimestamp, setForecastTimestamp] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [routeConfig, setRouteConfig] = useState<RouteGuidanceConfigResponse | null>(null);
  const [isGraphLoading, setIsGraphLoading] = useState(true);
  const [isRoutesLoading, setIsRoutesLoading] = useState(false);
  const [graphError, setGraphError] = useState<string | null>(null);
  const latestRouteRequestRef = useRef(0);

  const monthLabel = routeConfig?.month_label ?? "October";
  const currentSelectionOptions = routeConfig?.selection_options[year] ?? EMPTY_SELECTION_OPTIONS;
  const minDate = currentSelectionOptions.min_date;
  const maxDate = currentSelectionOptions.max_date;
  const availableTimes = currentSelectionOptions.times;
  const availableDates = currentSelectionOptions.available_dates;

  const requestRoutes = useCallback(
    async ({
      originId,
      destinationId,
      algorithmId,
      yearKey,
      routeCount,
      date,
      time,
      silentError = false,
    }: {
      originId: string;
      destinationId: string;
      algorithmId: AlgorithmId;
      yearKey: DataKey;
      routeCount: number;
      date: string | null;
      time: string | null;
      silentError?: boolean;
    }) => {
      if (!originId || !destinationId) {
        if (!silentError) {
          toast("Select both origin and destination before searching.", "error");
        }
        return;
      }

      if (originId === destinationId) {
        if (!silentError) {
          toast("Origin and destination must be different SCATS IDs.", "error");
        }
        return;
      }

      if (!date || !time) {
        if (!silentError) {
          toast("Pick a date and time before searching.", "error");
        }
        return;
      }

      if (availableDates.length > 0 && !availableDates.includes(date)) {
        if (!silentError) {
          toast("That date is outside the supported prediction range for the selected year.", "error");
        }
        return;
      }

      const requestId = ++latestRouteRequestRef.current;
      setIsRoutesLoading(true);

      try {
        const response = await fetchRoutes({
          origin: originId,
          destination: destinationId,
          k: routeCount,
          algorithm: algorithmId,
          data: yearKey,
          date,
          time,
        });

        if (requestId !== latestRouteRequestRef.current) {
          return;
        }

        setRoutes(response.routes);
        setForecastTimestamp(response.forecast_timestamp);
        setSelectedRoute(0);
        setShowDetails(response.routes.length > 0);

        if (!response.routes.length && !silentError) {
          toast("The backend did not return any routes for that SCATS pair.", "info");
        }
      } catch (error) {
        if (requestId !== latestRouteRequestRef.current) {
          return;
        }

        const message = error instanceof Error ? error.message : "Unknown backend error";
        setRoutes([]);
        setForecastTimestamp(null);
        setShowDetails(false);

        if (!silentError) {
          toast(`Route search failed: ${message}`, "error");
        }
      } finally {
        if (requestId === latestRouteRequestRef.current) {
          setIsRoutesLoading(false);
        }
      }
    },
    [availableDates, toast],
  );

  useEffect(() => {
    const abortController = new AbortController();

    async function loadRouteGuidanceContext() {
      setIsGraphLoading(true);
      setGraphError(null);

      try {
        const config = await fetchRouteGuidanceConfig(abortController.signal);
        setRouteConfig(config);
        setYear(config.defaults.data);
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }

        const message = error instanceof Error ? error.message : "Unknown backend error";
        setIsGraphLoading(false);
        setGraphError(message);
        setNodes([]);
        setEdges([]);
        setRoutes([]);
        setForecastTimestamp(null);
        toast(`Could not load graph data: ${message}`, "error");
      }
    }

    void loadRouteGuidanceContext();

    return () => {
      abortController.abort();
    };
  }, [toast]);

  useEffect(() => {
    if (!routeConfig) {
      return;
    }

    const abortController = new AbortController();

    async function loadGraphForYear() {
      setIsGraphLoading(true);
      setGraphError(null);

      try {
        const graph = await fetchGraph(year, abortController.signal);
        setNodes(graph.nodes);
        setEdges(graph.edges);

        const graphNodeIds = new Set(graph.nodes.map((node) => node.id));
        const nextOrigin = graphNodeIds.has(origin) ? origin : graph.nodes[0]?.id ?? "";
        const destinationCandidate = graphNodeIds.has(destination)
          ? destination
          : graph.nodes[Math.floor(graph.nodes.length / 2)]?.id ?? graph.nodes[1]?.id ?? "";
        const nextDestination =
          destinationCandidate && destinationCandidate !== nextOrigin
            ? destinationCandidate
            : graph.nodes.find((node) => node.id !== nextOrigin)?.id ?? "";

        setOrigin(nextOrigin);
        setDestination(nextDestination);
      } catch (error) {
        if (abortController.signal.aborted) {
          return;
        }

        const message = error instanceof Error ? error.message : "Unknown backend error";
        setGraphError(message);
        setNodes([]);
        setEdges([]);
        toast(`Could not load graph data: ${message}`, "error");
      } finally {
        if (!abortController.signal.aborted) {
          setIsGraphLoading(false);
        }
      }
    }

    const nextSelectionOptions = routeConfig.selection_options[year];
    const nextDate = nextSelectionOptions.default_date ?? nextSelectionOptions.available_dates[0] ?? "";
    const nextTime = nextSelectionOptions.default_time ?? nextSelectionOptions.times[0] ?? "";
    setSelectedDate(nextDate);
    setSelectedTime(nextTime);
    setRoutes([]);
    setForecastTimestamp(null);

    void loadGraphForYear();

    return () => {
      abortController.abort();
    };
  }, [routeConfig, year]);

  useEffect(() => {
    if (!selectedDate && availableDates.length > 0) {
      setSelectedDate(availableDates[0]);
      return;
    }

    if (selectedDate && availableDates.length > 0 && !availableDates.includes(selectedDate)) {
      setSelectedDate(availableDates[0] ?? "");
    }
  }, [availableDates, selectedDate]);

  useEffect(() => {
    if (!selectedTime && availableTimes.length > 0) {
      setSelectedTime(availableTimes[0]);
      return;
    }

    if (selectedTime && !availableTimes.includes(selectedTime)) {
      setSelectedTime(availableTimes[0] ?? "");
    }
  }, [availableTimes, selectedTime]);

  useEffect(() => {
    if (origin && destination && origin !== destination && !isGraphLoading && selectedDate && selectedTime) {
      void requestRoutes({
        originId: origin,
        destinationId: destination,
        algorithmId: algorithm,
        yearKey: year,
        routeCount: topK,
        date: selectedDate,
        time: selectedTime,
        silentError: true,
      });
    }
  }, [origin, destination, algorithm, year, topK, isGraphLoading, requestRoutes, selectedDate, selectedTime]);

  const handleDateChange = useCallback(
    (nextDate: string) => {
      setSelectedDate(nextDate);
      if (availableDates.length > 0 && !availableDates.includes(nextDate)) {
        toast("That date is outside the supported prediction range for the selected year.", "error");
      }
    },
    [availableDates, toast],
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
    [selectingFor],
  );

  if (isGraphLoading && !nodes.length) {
    return (
      <div className="flex h-full min-h-screen items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4 text-slate-500">
          <LoaderCircle className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-sm font-medium">Loading SCATS graph from backend...</p>
        </div>
      </div>
    );
  }

  if (graphError) {
    return (
      <div className="flex h-full min-h-screen items-center justify-center font-sans p-8">
        <div className="flex flex-col items-center gap-3 text-center max-w-sm">
          <ServerCrash className="w-8 h-8 text-red-400" />
          <p className="text-sm font-semibold text-slate-700">Could not load graph data</p>
          <p className="text-xs text-slate-400">{graphError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[1500px] w-full min-h-screen font-sans">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
        <motion.div variants={item}>
          <h1 className="text-[26px] font-bold tracking-tight text-slate-800">Route Guidance</h1>
          <p className="text-[14px] text-slate-500 font-medium mt-1">
            Find optimal travel routes using backend ML predictions. Pick a year, date, and time in October, then click nodes on the map or type SCATS IDs.
          </p>
          {forecastTimestamp && (
            <p className="text-[12px] text-slate-400 font-medium mt-2">
              Forecast snapshot: <span className="text-slate-600 font-semibold">{forecastTimestamp}</span>
            </p>
          )}
        </motion.div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
          <div className="xl:col-span-4 space-y-4">
            <RouteControls
              origin={origin}
              destination={destination}
              topK={topK}
              algorithm={algorithm}
              year={year}
              onOriginChange={setOrigin}
              onDestinationChange={setDestination}
              onTopKChange={setTopK}
              onAlgorithmChange={setAlgorithm}
              onYearChange={setYear}
              monthLabel={monthLabel}
              selectedDate={selectedDate}
              selectedTime={selectedTime}
              minDate={minDate}
              maxDate={maxDate}
              availableTimes={availableTimes}
              onDateChange={handleDateChange}
              onTimeChange={setSelectedTime}
              onFindRoutes={() => {
                void requestRoutes({
                  originId: origin,
                  destinationId: destination,
                  algorithmId: algorithm,
                  yearKey: year,
                  routeCount: topK,
                  date: selectedDate,
                  time: selectedTime,
                });
              }}
              onSelectOrigin={() => setSelectingFor(selectingFor === "origin" ? null : "origin")}
              onSelectDestination={() => setSelectingFor(selectingFor === "destination" ? null : "destination")}
              selectingFor={selectingFor}
              routes={routes}
              selectedRoute={selectedRoute}
              onSelectRoute={(index) => {
                setSelectedRoute(index);
                setShowDetails(true);
              }}
              isGraphLoading={isGraphLoading}
              isRoutesLoading={isRoutesLoading}
            />
          </div>

          <div className="xl:col-span-8 space-y-6">
            <motion.div variants={item}>
              <div className="bg-white rounded-[24px] shadow-sm border border-slate-200/60 h-[580px] relative overflow-hidden p-0">
                <CityMap
                  nodes={nodes}
                  edges={edges}
                  routes={routes}
                  selectedRoute={selectedRoute}
                  origin={origin}
                  destination={destination}
                  onNodeClick={handleNodeClick}
                  onSelectRoute={(index) => {
                    setSelectedRoute(index);
                    setShowDetails(true);
                  }}
                  selectingFor={selectingFor}
                />

                {isRoutesLoading && (
                  <div className="absolute top-6 left-6 z-[1000] rounded-full border border-blue-100 bg-white/95 px-4 py-2 text-sm text-blue-600 flex items-center gap-2 shadow-sm">
                    <LoaderCircle className="w-4 h-4 animate-spin" />
                    Finding routes...
                  </div>
                )}

                <div className="absolute bottom-6 left-6 p-4 text-[13px] text-slate-500 font-medium space-y-2.5 pointer-events-none">
                  <div className="flex items-center gap-2.5">
                    <div className="w-3.5 h-3.5 rounded-full bg-blue-600 shadow-sm" />
                    <span>Origin</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-3.5 h-3.5 rounded-full bg-red-500 shadow-sm" />
                    <span>Destination</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-[4px] rounded-full bg-blue-600 shadow-sm" />
                    <span>Selected Route</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-[3px] rounded-full bg-slate-400 opacity-60" style={{ backgroundImage: "repeating-linear-gradient(to right, #9ca3af 0 6px, transparent 6px 10px)" }} />
                    <span>Other Routes</span>
                  </div>
                </div>

                <div className="absolute top-6 right-6 text-[13px] text-slate-500 font-bold flex items-center gap-3 pointer-events-none">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{nodes.length} nodes</span>
                  </span>
                  <span className="w-[1.5px] h-3.5 bg-slate-300" />
                  <span>{monthLabel}</span>
                  <span className="w-[1.5px] h-3.5 bg-slate-300" />
                  <span className="uppercase">{algorithm}</span>
                </div>
              </div>
            </motion.div>

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
