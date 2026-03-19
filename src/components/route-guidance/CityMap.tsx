import { useMemo, useState, useCallback } from "react";
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
      if (node.id === origin) return "#2563eb"; 
      if (node.id === destination) return "#ff0000ff";
      if (activeRouteNodes.has(node.id)) return "#93c5fd";
      return "#e2e8f0";
    },
    [origin, destination, activeRouteNodes]
  );

  const getNodeRadius = useCallback(
    (node: MapNode) => {
      if (node.id === origin || node.id === destination) return 6;
      if (hoveredNode === node.id) return 5;
      if (activeRouteNodes.has(node.id)) return 4;
      return 2.5;
    },
    [origin, destination, hoveredNode, activeRouteNodes]
  );

  return (
    <svg viewBox="0 0 960 640" className="w-full h-full" style={{ cursor: selectingFor ? "crosshair" : "default" }}>
      <defs>
        <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#2563eb" />
          <stop offset="100%" stopColor="#0004fcff" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Road network */}
      {uniqueEdges.map((edge) => {
        const from = nodeMap[edge.from];
        const to = nodeMap[edge.to];
        if (!from || !to) return null;
        const isOnRoute = routeEdgeSet.has(`${edge.from}-${edge.to}`);
        return (
          <line
            key={`${edge.from}-${edge.to}`}
            x1={from.x}
            y1={from.y}
            x2={to.x}
            y2={to.y}
            stroke={isOnRoute ? "#cbd5e1" : "#f1f5f9"}
            strokeWidth={isOnRoute ? 1.5 : 1}
            opacity={isOnRoute ? 0.8 : 0.6}
          />
        );
      })}

      {/* Alternative routes (render first so optimal route is on top) */}
      {routes.map((route, ri) => {
        if (ri === selectedRoute) return null; // Render selected later
        const points = route.nodes
          .map((id) => nodeMap[id])
          .filter(Boolean)
          .map((n) => `${n.x},${n.y}`)
          .join(" ");
        return (
          <polyline
            key={ri}
            points={points}
            fill="none"
            stroke={ROUTE_COLORS[Math.min(ri, ROUTE_COLORS.length - 1)]}
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.4}
          />
        );
      })}

      {/* Active route */}
      {routes[selectedRoute] && (
        <polyline
          points={routes[selectedRoute].nodes
            .map((id) => nodeMap[id])
            .filter(Boolean)
            .map((n) => `${n.x},${n.y}`)
            .join(" ")}
          fill="none"
          stroke="url(#routeGrad)"
          strokeWidth={4.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.9}
          filter="url(#glow)"
        />
      )}

      {/* Nodes */}
      {nodes.map((node) => {
        const isHovered = hoveredNode === node.id;
        const isOrigin = node.id === origin;
        const isDest = node.id === destination;

        return (
          <g
            key={node.id}
            onClick={() => onNodeClick?.(node.id)}
            onMouseEnter={() => setHoveredNode(node.id)}
            onMouseLeave={() => setHoveredNode(null)}
            style={{ cursor: selectingFor ? "crosshair" : "pointer" }}
          >
            <circle
              cx={node.x}
              cy={node.y}
              r={getNodeRadius(node) + 6}
              fill="transparent"
            />
            <circle
              cx={node.x}
              cy={node.y}
              r={getNodeRadius(node)}
              fill={getNodeColor(node)}
              stroke={isOrigin || isDest ? "#ffffff" : "none"}
              strokeWidth={isOrigin || isDest ? 2 : 0}
            />

            {/* Render all labels faintly, but make active/hovered ones darker */}
            <text
              x={node.x}
              y={node.y - 8}
              textAnchor="middle"
              fontSize={isOrigin || isDest || isHovered ? "10" : "8"}
              fill={isOrigin || isDest || isHovered ? "#475569" : "#94a3b8"}
              fontFamily="sans-serif"
              fontWeight={isOrigin || isDest || isHovered ? 600 : 500}
              letterSpacing="-0.02em"
            >
              {node.label}
            </text>

            {/* Origin/Dest pulse */}
            {(isOrigin || isDest) && (
              <circle
                cx={node.x}
                cy={node.y}
                r={12}
                fill="none"
                stroke={isOrigin ? "#2563eb" : "#ff0000ff"}
                strokeWidth={1.5}
                opacity={0.3}
              >
                <animate attributeName="r" values="8;20;8" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.4;0;0.4" dur="2s" repeatCount="indefinite" />
              </circle>
            )}
          </g>
        );
      })}

      {/* Selecting hint */}
      {selectingFor && (
        <text x="480" y="625" textAnchor="middle" fontSize="13" fontWeight="500" fill="#2563eb" fontFamily="sans-serif">
          Click a node to set {selectingFor}
        </text>
      )}
    </svg>
  );
}
