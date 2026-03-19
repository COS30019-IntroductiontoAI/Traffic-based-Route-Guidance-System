// Large city road network with ~60 nodes
export interface MapNode {
  id: string;
  x: number;
  y: number;
  label: string;
}

export interface MapEdge {
  from: string;
  to: string;
  weight: number; // travel time in minutes
}

// Generate a grid-like city with some diagonal roads
const createNodes = (): MapNode[] => {
  const nodes: MapNode[] = [];
  const cols = 10;
  const rows = 7;
  const xSpacing = 90;
  const ySpacing = 85;
  const offsetX = 60;
  const offsetY = 50;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const jitterX = (Math.sin(r * 3 + c * 7) * 12);
      const jitterY = (Math.cos(r * 5 + c * 2) * 10);
      nodes.push({
        id: `${4000 + r * 100 + c}`,
        x: offsetX + c * xSpacing + jitterX,
        y: offsetY + r * ySpacing + jitterY,
        label: `${4000 + r * 100 + c}`,
      });
    }
  }
  return nodes;
};

const createEdges = (nodes: MapNode[]): MapEdge[] => {
  const edges: MapEdge[] = [];
  const cols = 10;
  const rows = 7;

  const getId = (r: number, c: number) => `${4000 + r * 100 + c}`;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      // Horizontal
      if (c < cols - 1) {
        const w = 1 + Math.random() * 3;
        edges.push({ from: getId(r, c), to: getId(r, c + 1), weight: Math.round(w * 10) / 10 });
        edges.push({ from: getId(r, c + 1), to: getId(r, c), weight: Math.round(w * 10) / 10 });
      }
      // Vertical
      if (r < rows - 1) {
        const w = 1 + Math.random() * 3;
        edges.push({ from: getId(r, c), to: getId(r + 1, c), weight: Math.round(w * 10) / 10 });
        edges.push({ from: getId(r + 1, c), to: getId(r, c), weight: Math.round(w * 10) / 10 });
      }
      // Some diagonals for realism
      if (r < rows - 1 && c < cols - 1 && (r + c) % 3 === 0) {
        const w = 1.5 + Math.random() * 3;
        edges.push({ from: getId(r, c), to: getId(r + 1, c + 1), weight: Math.round(w * 10) / 10 });
        edges.push({ from: getId(r + 1, c + 1), to: getId(r, c), weight: Math.round(w * 10) / 10 });
      }
    }
  }
  return edges;
};

export const cityNodes = createNodes();
export const cityEdges = createEdges(cityNodes);

// Dijkstra's algorithm
export function findShortestPaths(
  nodes: MapNode[],
  edges: MapEdge[],
  originId: string,
  destId: string,
  topK: number
): { nodes: string[]; time: number; distance: number }[] {
  const adj: Record<string, { to: string; weight: number }[]> = {};
  for (const n of nodes) adj[n.id] = [];
  for (const e of edges) {
    if (adj[e.from]) adj[e.from].push({ to: e.to, weight: e.weight });
  }

  const results: { nodes: string[]; time: number }[] = [];

  // Yen's K-shortest paths (simplified)
  const dijkstra = (
    blocked: Set<string>
  ): { path: string[]; cost: number } | null => {
    const dist: Record<string, number> = {};
    const prev: Record<string, string | null> = {};
    const visited = new Set<string>();

    for (const n of nodes) dist[n.id] = Infinity;
    dist[originId] = 0;
    prev[originId] = null;

    const queue = [...nodes.map((n) => n.id)].filter((id) => !blocked.has(id) || id === originId || id === destId);

    while (queue.length > 0) {
      queue.sort((a, b) => dist[a] - dist[b]);
      const u = queue.shift()!;
      if (visited.has(u)) continue;
      visited.add(u);
      if (dist[u] === Infinity) break;

      for (const neighbor of adj[u] || []) {
        if (blocked.has(`${u}-${neighbor.to}`)) continue;
        const alt = dist[u] + neighbor.weight;
        if (alt < dist[neighbor.to]) {
          dist[neighbor.to] = alt;
          prev[neighbor.to] = u;
        }
      }
    }

    if (dist[destId] === Infinity) return null;

    const path: string[] = [];
    let current: string | null = destId;
    while (current) {
      path.unshift(current);
      current = prev[current];
    }
    return { path, cost: dist[destId] };
  };

  // Find first shortest path
  const first = dijkstra(new Set());
  if (!first) return [];
  results.push({ nodes: first.path, time: first.cost });

  // Find alternative paths by blocking edges
  for (let k = 1; k < topK; k++) {
    const prevPath = results[k - 1].nodes;
    let bestAlt: { path: string[]; cost: number } | null = null;

    for (let i = 0; i < prevPath.length - 1; i++) {
      const blocked = new Set<string>();
      // Block edges used by previous paths at this spur node
      for (const r of results) {
        if (r.nodes.slice(0, i + 1).join(",") === prevPath.slice(0, i + 1).join(",")) {
          blocked.add(`${r.nodes[i]}-${r.nodes[i + 1]}`);
        }
      }

      const alt = dijkstra(blocked);
      if (alt && (!bestAlt || alt.cost < bestAlt.cost)) {
        const isDuplicate = results.some((r) => r.nodes.join(",") === alt.path.join(","));
        if (!isDuplicate) bestAlt = alt;
      }
    }

    if (bestAlt) {
      results.push({ nodes: bestAlt.path, time: bestAlt.cost });
    }
  }

  return results.map((r, i) => ({
    nodes: r.nodes,
    time: Math.round(r.time * 10) / 10,
    distance: Math.round(r.nodes.length * 1.2 * 10) / 10,
  }));
}
