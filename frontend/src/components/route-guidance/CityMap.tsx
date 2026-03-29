import { useMemo, useState, useCallback, useEffect, useRef } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { MapNode, MapEdge, RouteResult } from "./cityMapData";

interface CityMapProps {
  nodes: MapNode[];
  edges: MapEdge[];
  routes: RouteResult[];
  selectedRoute: number;
  origin: string;
  destination: string;
  onNodeClick?: (nodeId: string) => void;
  onSelectRoute?: (index: number) => void;
  selectingFor?: "origin" | "destination" | null;
}


const DEFAULT_CENTER: [number, number] = [-37.82, 145.045];
const DEFAULT_ZOOM = 13;

// Only fits the map to all nodes once on initial load — never auto-zooms after that.
function InitialMapFit({ nodes }: { nodes: MapNode[] }) {
  const map = useMap();
  const hasFit = useRef(false);

  useEffect(() => {
    if (hasFit.current || nodes.length === 0) return;

    // Filter out outlier nodes (coordinates far from Boroondara, Melbourne)
    const boroondara = nodes.filter(
      (n) => n.lat > -38.1 && n.lat < -37.6 && n.lng > 144.8 && n.lng < 145.3,
    );
    const validNodes = boroondara.length > 0 ? boroondara : nodes;

    const lats = validNodes.map((n) => n.lat);
    const lngs = validNodes.map((n) => n.lng);

    map.fitBounds(
      [
        [Math.min(...lats), Math.min(...lngs)],
        [Math.max(...lats), Math.max(...lngs)],
      ],
      { padding: [40, 40], animate: false },
    );
    hasFit.current = true;
  }, [map, nodes]);

  return null;
}

export function CityMap({
  nodes,
  edges,
  routes,
  selectedRoute,
  origin,
  destination,
  onNodeClick,
  onSelectRoute,
  selectingFor,
}: CityMapProps) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const nodeMap = useMemo(() => {
    const result: Record<string, MapNode> = {};
    for (const node of nodes) {
      result[node.id] = node;
    }
    return result;
  }, [nodes]);

  const uniqueEdges = useMemo(() => {
    const seen = new Set<string>();
    return edges.filter((edge) => {
      const key = [edge.from, edge.to].sort().join("-");
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }, [edges]);

  const activeRouteNodes = useMemo(() => {
    const result = new Set<string>();
    if (routes[selectedRoute]) {
      for (const nodeId of routes[selectedRoute].nodes) {
        result.add(nodeId);
      }
    }
    return result;
  }, [routes, selectedRoute]);

  const getNodeColor = useCallback(
    (node: MapNode) => {
      if (node.id === origin) {
        return "#2563eb"; // Blue for origin
      }
      if (node.id === destination) {
        return "#ef4444"; // Red for destination
      }
      if (activeRouteNodes.has(node.id)) {
        return "#3b82f6"; // Light blue for nodes on selected route
      }
      return "#cbd5e1"; // Slate for inactive nodes
    },
    [origin, destination, activeRouteNodes],
  );

  const getNodeRadius = useCallback(
    (node: MapNode) => {
      if (node.id === origin || node.id === destination) {
        return 9;
      }
      if (hoveredNode === node.id) {
        return 7;
      }
      if (activeRouteNodes.has(node.id)) {
        return 6;
      }
      return 4;
    },
    [origin, destination, hoveredNode, activeRouteNodes],
  );

  const dragBounds: LatLngBoundsExpression = useMemo(() => {
    // Use only nodes that are plausibly within Victoria, Australia
    const validNodes = nodes.filter(
      (n) => n.lat > -39.5 && n.lat < -33.5 && n.lng > 140.0 && n.lng < 150.5,
    );

    if (validNodes.length === 0) {
      const [lat, lng] = DEFAULT_CENTER;
      const buffer = 0.1;
      return [
        [lat - buffer, lng - buffer],
        [lat + buffer, lng + buffer],
      ];
    }

    const lats = validNodes.map((node) => node.lat);
    const lngs = validNodes.map((node) => node.lng);
    const latBuffer = 0.06;
    const lngBuffer = 0.08;

    return [
      [Math.min(...lats) - latBuffer, Math.min(...lngs) - lngBuffer],
      [Math.max(...lats) + latBuffer, Math.max(...lngs) + lngBuffer],
    ];
  }, [nodes]);

  return (
    <div className="w-full h-full relative" style={{ cursor: selectingFor ? "crosshair" : "default" }}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        minZoom={12}
        maxZoom={16}
        maxBounds={dragBounds}
        maxBoundsViscosity={0.8}
        className="w-full h-full z-0"
        zoomControl={true}
        preferCanvas
      >
        <InitialMapFit nodes={nodes} />

        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {uniqueEdges.map((edge) => {
          const from = nodeMap[edge.from];
          const to = nodeMap[edge.to];
          if (!from || !to) {
            return null;
          }

          return (
            <Polyline
              key={`base-${edge.from}-${edge.to}`}
              positions={[[from.lat, from.lng], [to.lat, to.lng]]}
              pathOptions={{
                color: "#d1d5db",
                weight: 1.5,
                opacity: 0.5,
              }}
            />
          );
        })}

         {/* Unselected (alternative) routes — all rendered in neutral grey */}
        {routes.map((route, routeIndex) => {
          if (routeIndex === selectedRoute) {
            return null; // draw selected route last so it renders on top
          }

          const positions = route.nodes
            .map((nodeId) => nodeMap[nodeId])
            .filter((node): node is MapNode => Boolean(node))
            .map((node) => [node.lat, node.lng] as [number, number]);

          return (
            <Polyline
              key={`alt-route-${route.rank ?? routeIndex}`}
              positions={positions}
              pathOptions={{
                color: "#9ca3af",   // fixed grey for every non-selected route
                weight: 5,          // increased weight slightly for easier clicking
                opacity: 0.5,
                dashArray: "6 4",
                className: "cursor-pointer hover:stroke-slate-500", // adding cursor pointer and hover color
              }}
              eventHandlers={{
                click: () => onSelectRoute?.(routeIndex),
                mouseover: (e) => {
                  const layer = e.target;
                  layer.setStyle({ color: "#64748b", opacity: 0.8 }); // slate-500 equivalent
                },
                mouseout: (e) => {
                  const layer = e.target;
                  layer.setStyle({ color: "#9ca3af", opacity: 0.5 }); // original color
                }
              }}
            >
              <Tooltip sticky>
                Alternative Route {routeIndex}
              </Tooltip>
            </Polyline>
          );
        })}

        {/* Selected route — one solid blue line, always on top */}
        {routes[selectedRoute] && (
          <Polyline
            positions={routes[selectedRoute].nodes
              .map((nodeId) => nodeMap[nodeId])
              .filter((node): node is MapNode => Boolean(node))
              .map((node) => [node.lat, node.lng] as [number, number])}
            pathOptions={{
              color: "#2563eb",  // solid blue — single colour for the chosen route
              weight: 6,
              opacity: 0.92,
              lineCap: "round",
              lineJoin: "round",
            }}
          />
        )}

        {nodes.map((node) => {
          const isOrigin = node.id === origin;
          const isDestination = node.id === destination;
          const radius = getNodeRadius(node);

          return (
            <CircleMarker
              key={node.id}
              center={[node.lat, node.lng]}
              radius={radius}
              pathOptions={{
                fillColor: getNodeColor(node),
                fillOpacity: 1,
                color: isOrigin || isDestination ? "#ffffff" : "#475569",
                weight: isOrigin || isDestination ? 2 : 1,
              }}
              eventHandlers={{
                click: () => onNodeClick?.(node.id),
                mouseover: () => setHoveredNode(node.id),
                mouseout: () => setHoveredNode(null),
              }}
            >
              <Tooltip direction="top" offset={[0, -radius - 2]} opacity={1}>
                {node.id}
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {selectingFor && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] bg-white/90 backdrop-blur shadow-md px-4 py-2 rounded-full font-sans text-[13px] font-medium text-blue-600 border border-blue-100 flex items-center gap-2 pointer-events-none">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          Click a node on the map to set {selectingFor}
        </div>
      )}
    </div>
  );
}
