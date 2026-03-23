import { useMemo, useState, useCallback, useEffect } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { MapNode, MapEdge } from "./cityMapData";

interface CityMapProps {
  nodes: MapNode[];
  edges: MapEdge[];
  routes: { nodes: string[]; time: number; distance: number }[];
  selectedRoute: number;
  origin: string;
  destination: string;
  onNodeClick?: (nodeId: string) => void;
  selectingFor?: "origin" | "destination" | null;
}

const ROUTE_COLORS = [
  "#2563eb", // blue-600 for Optimal Route
  "#10b981", // emerald-500 for Alternative 1
  "#8b5cf6", // violet-500 for Alternative 2
  "#3b82f6", // blue-500
  "#f59e0b", // amber-500
];

const MapBounds = ({ nodes, routes, selectedRoute, nodeMap }: { nodes: MapNode[], routes: any[], selectedRoute: number, nodeMap: Record<string, MapNode> }) => {
  const map = useMap();
  useEffect(() => {
    if (routes && routes[selectedRoute]) {
      const routeNodes = routes[selectedRoute].nodes;
      const lats = routeNodes.map((n: string) => nodeMap[n]?.lat).filter(Boolean);
      const lngs = routeNodes.map((n: string) => nodeMap[n]?.lng).filter(Boolean);
      if (lats.length > 0 && lngs.length > 0) {
        map.flyToBounds([
          [Math.min(...lats), Math.min(...lngs)],
          [Math.max(...lats), Math.max(...lngs)]
        ], { padding: [50, 50], duration: 1.2 });
        return;
      }
    }
    
    // Fallback to bounding all nodes if no route is active
    if (nodes.length > 0) {
      const lats = nodes.map(n => n.lat);
      const lngs = nodes.map(n => n.lng);
      map.fitBounds([
        [Math.min(...lats), Math.min(...lngs)],
        [Math.max(...lats), Math.max(...lngs)]
      ], { padding: [30, 30] });
    }
  }, [map, nodes, routes, selectedRoute, nodeMap]);
  return null;
};

export function CityMap({
  nodes,
  edges,
  routes,
  selectedRoute,
  origin,
  destination,
  onNodeClick,
  selectingFor,
}: CityMapProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const nodeMap = useMemo(() => {
    const m: Record<string, MapNode> = {};
    for (const n of nodes) m[n.id] = n;
    return m;
  }, [nodes]);

  // Unique edges for rendering (deduplicate bidirectional)
  const uniqueEdges = useMemo(() => {
    const seen = new Set<string>();
    return edges.filter((e) => {
      const key = [e.from, e.to].sort().join("-");
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [edges]);

  const activeRouteNodes = useMemo(() => {
    const s = new Set<string>();
    if (routes[selectedRoute]) {
      for (const n of routes[selectedRoute].nodes) s.add(n);
    }
    return s;
  }, [routes, selectedRoute]);

  const routeEdgeSet = useMemo(() => {
    const s = new Set<string>();
    for (const route of routes) {
      for (let i = 0; i < route.nodes.length - 1; i++) {
        s.add(`${route.nodes[i]}-${route.nodes[i + 1]}`);
        s.add(`${route.nodes[i + 1]}-${route.nodes[i]}`);
      }
    }
    return s;
  }, [routes]);

  const getNodeColor = useCallback(
    (node: MapNode) => {
      if (node.id === origin) return "#2563eb"; // blue-600
      if (node.id === destination) return "#ef4444"; // red-500
      if (activeRouteNodes.has(node.id)) return "#93c5fd"; // blue-300
      return "#cbd5e1"; // slate-300
    },
    [origin, destination, activeRouteNodes]
  );

  const getNodeRadius = useCallback(
    (node: MapNode) => {
      if (node.id === origin || node.id === destination) return 8;
      if (hoveredNode === node.id) return 7;
      if (activeRouteNodes.has(node.id)) return 6;
      return 5;
    },
    [origin, destination, hoveredNode, activeRouteNodes]
  );

  return (
    <div className="w-full h-full relative" style={{ cursor: selectingFor ? "crosshair" : "default" }}>
      <MapContainer
        center={[-37.8136, 144.9631]} // Default will be updated by MapBounds
        zoom={14}
        className="w-full h-full z-0"
        zoomControl={false}
        preferCanvas={true}
      >
        <MapBounds nodes={nodes} routes={routes} selectedRoute={selectedRoute} nodeMap={nodeMap} />
        
        {/* Realistic Base Map - OpenStreetMap Light Mode tiles */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {/* Base Road Network layer */}
        {uniqueEdges.map((edge) => {
          const from = nodeMap[edge.from];
          const to = nodeMap[edge.to];
          if (!from || !to) return null;
          const isOnRoute = routeEdgeSet.has(`${edge.from}-${edge.to}`);
          return (
            <Polyline
              key={`base-${edge.from}-${edge.to}`}
              positions={[[from.lat, from.lng], [to.lat, to.lng]]}
              pathOptions={{
                color: isOnRoute ? "#94a3b8" : "#cbd5e1",
                weight: isOnRoute ? 2 : 1.5,
                opacity: isOnRoute ? 0.7 : 0.5,
              }}
            />
          );
        })}

        {/* Alternative Routes */}
        {routes.map((route, ri) => {
          if (ri === selectedRoute) return null; // Default rendered later
          const positions = route.nodes
            .map((id) => nodeMap[id])
            .filter(Boolean)
            .map((n) => [n.lat, n.lng] as [number, number]);
          
          return (
            <Polyline
              key={`alt-route-${ri}`}
              positions={positions}
              pathOptions={{
                color: ROUTE_COLORS[Math.min(ri, ROUTE_COLORS.length - 1)],
                weight: 4,
                opacity: 0.5,
                className: "route-flow-alt",
              }}
            />
          );
        })}

        {/* Active Route */}
        {routes[selectedRoute] && (
          <Polyline
            positions={routes[selectedRoute].nodes
              .map((id) => nodeMap[id])
              .filter(Boolean)
              .map((n) => [n.lat, n.lng] as [number, number])}
            pathOptions={{
              color: "#2563eb",
              weight: 6,
              opacity: 0.9,
              className: "route-flow",
            }}
          />
        )}

        {/* Rendering Intersections / Nodes */}
        {nodes.map((node) => {
          const isOrigin = node.id === origin;
          const isDest = node.id === destination;
          const radius = getNodeRadius(node);

          return (
            <CircleMarker
              key={node.id}
              center={[node.lat, node.lng]}
              radius={radius}
              pathOptions={{
                fillColor: getNodeColor(node),
                fillOpacity: 1,
                color: isOrigin || isDest ? "#ffffff" : "#475569",
                weight: isOrigin || isDest ? 2 : 1,
              }}
              eventHandlers={{
                click: () => onNodeClick?.(node.id),
                mouseover: () => setHoveredNode(node.id),
                mouseout: () => setHoveredNode(null),
              }}
            >
              <Tooltip direction="top" offset={[0, -radius - 2]} opacity={1}>
                {node.label}
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Selecting hint overlay */}
      {selectingFor && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur shadow-md px-4 py-2 rounded-full font-sans text-[13px] font-medium text-blue-600 border border-blue-100 flex items-center gap-2 pointer-events-none">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Click a node on the map to set {selectingFor}
        </div>
      )}
    </div>
  );
}
