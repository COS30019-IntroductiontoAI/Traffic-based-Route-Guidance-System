import { useMemo, useState, useCallback, useEffect } from "react";
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
  selectingFor?: "origin" | "destination" | null;
}


const DEFAULT_CENTER: [number, number] = [-37.82, 145.045];

function MapBounds({
  nodes,
  routes,
  selectedRoute,
  nodeMap,
}: {
  nodes: MapNode[];
  routes: RouteResult[];
  selectedRoute: number;
  nodeMap: Record<string, MapNode>;
}) {
  const map = useMap();

  useEffect(() => {
    if (routes[selectedRoute]) {
      const routeNodes = routes[selectedRoute].nodes;
      const lats = routeNodes
        .map((nodeId) => nodeMap[nodeId]?.lat)
        .filter((value): value is number => value !== undefined);
      const lngs = routeNodes
        .map((nodeId) => nodeMap[nodeId]?.lng)
        .filter((value): value is number => value !== undefined);

      if (lats.length > 0 && lngs.length > 0) {
        map.flyToBounds(
          [
            [Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)],
          ],
          { padding: [50, 50], duration: 1.2 },
        );
        return;
      }
    }

    if (nodes.length > 0) {
      const lats = nodes.map((node) => node.lat);
      const lngs = nodes.map((node) => node.lng);

      map.fitBounds(
        [
          [Math.min(...lats), Math.min(...lngs)],
          [Math.max(...lats), Math.max(...lngs)],
        ],
        { padding: [30, 30] },
      );
    }
  }, [map, nodes, routes, selectedRoute, nodeMap]);

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
        return "#2563eb";
      }
      if (node.id === destination) {
        return "#ef4444";
      }
      if (activeRouteNodes.has(node.id)) {
        return "#93c5fd";
      }
      return "#cbd5e1";
    },
    [origin, destination, activeRouteNodes],
  );

  const getNodeRadius = useCallback(
    (node: MapNode) => {
      if (node.id === origin || node.id === destination) {
        return 8;
      }
      if (hoveredNode === node.id) {
        return 7;
      }
      if (activeRouteNodes.has(node.id)) {
        return 6;
      }
      return 5;
    },
    [origin, destination, hoveredNode, activeRouteNodes],
  );

  const dragBounds: LatLngBoundsExpression = useMemo(() => {
    if (nodes.length === 0) {
      const [lat, lng] = DEFAULT_CENTER;
      const buffer = 0.1;
      return [
        [lat - buffer, lng - buffer],
        [lat + buffer, lng + buffer],
      ];
    }

    const lats = nodes.map((node) => node.lat);
    const lngs = nodes.map((node) => node.lng);
    const latBuffer = 0.04;
    const lngBuffer = 0.06;

    return [
      [Math.min(...lats) - latBuffer, Math.min(...lngs) - lngBuffer],
      [Math.max(...lats) + latBuffer, Math.max(...lngs) + lngBuffer],
    ];
  }, [nodes]);

  return (
    <div className="w-full h-full relative" style={{ cursor: selectingFor ? "crosshair" : "default" }}>
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={1}
        minZoom={12.5}
        maxZoom={13.5}
        maxBounds={dragBounds}
        maxBoundsViscosity={1}
        className="w-full h-full z-0"
        zoomControl={false}
        preferCanvas
      >
        <MapBounds nodes={nodes} routes={routes} selectedRoute={selectedRoute} nodeMap={nodeMap} />

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

        {routes.map((route, routeIndex) => {
          if (routeIndex === selectedRoute) {
            return null;
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
                color: "#9ca3af",
                weight: 4,
                opacity: 0.45,
              }}
            />
          );
        })}

        {routes[selectedRoute] && (
          <Polyline
            positions={routes[selectedRoute].nodes
              .map((nodeId) => nodeMap[nodeId])
              .filter((node): node is MapNode => Boolean(node))
              .map((node) => [node.lat, node.lng] as [number, number])}
            pathOptions={{
              color: "#f59e0b",
              weight: 6,
              opacity: 0.9,
              className: "route-flow",
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
