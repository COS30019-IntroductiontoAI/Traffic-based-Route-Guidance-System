// Large city road network with ~60 nodes
export interface MapNode {
  id: string;
  x: number;
  y: number;
  lat: number;
  lng: number;
  label: string;
}

export interface MapEdge {
  from: string;
  to: string;
  weight: number; // travel time in minutes
}

export interface RouteSegment {
  from: string;
  to: string;
  time: number;
  traffic: "clear" | "moderate" | "heavy";
}

export interface RouteResult {
  nodes: string[];
  time: number;
  distance: number;
  segments: RouteSegment[];
}

import nodesData from "./nodes.json";
import edgesData from "./edges.json";

// We import the real Boroondara graph we fetched from Overpass API
export const cityNodes: MapNode[] = nodesData as MapNode[];
export const cityEdges: MapEdge[] = edgesData as MapEdge[];

let precomputedAdj: Record<string, { to: string; weight: number }[]> | null = null;

function getAdjacencyList(nodes: MapNode[], edges: MapEdge[]) {
  if (precomputedAdj) return precomputedAdj;
  
  const adj: Record<string, { to: string; weight: number }[]> = {};
  for (const n of nodes) adj[n.id] = [];
  
  // 1. Add given edges (bidirectional to fix one-way islands)
  for (const e of edges) {
    if (adj[e.from]) adj[e.from].push({ to: e.to, weight: e.weight });
    if (adj[e.to] && !adj[e.to].some(x => x.to === e.from)) {
      adj[e.to].push({ to: e.from, weight: e.weight });
    }
  }

  // 2. Add 3-Nearest Neighbors to completely connect the graph
  const distance = (n1: MapNode, n2: MapNode) => {
    const dx = (n1.lng - n2.lng) * Math.cos(n1.lat * Math.PI / 180) * 111.32;
    const dy = (n1.lat - n2.lat) * 111.32;
    return Math.sqrt(dx * dx + dy * dy); // Approx dist in km
  };

  for (const n of nodes) {
    const neighbors = nodes
      .filter((other) => other.id !== n.id)
      .map((other) => ({ to: other.id, dist: distance(n, other) }))
      .sort((a, b) => a.dist - b.dist)
      .slice(0, 3);
      
      for (const neighbor of neighbors) {
      if (!adj[n.id].some((x) => x.to === neighbor.to)) {
        // According to requirements: 60km/h = 1 min per km + 30s (0.5 min) delay at intersection
        const weight = Math.max(0.1, neighbor.dist + 0.5); 
        adj[n.id].push({ to: neighbor.to, weight: Math.round(weight * 100) / 100 });
        adj[neighbor.to].push({ to: n.id, weight: Math.round(weight * 100) / 100 });
      }
    }
  }

  precomputedAdj = adj;
  return adj;
}

// Dijkstra's algorithm
export function findShortestPaths(
  nodes: MapNode[],
  edges: MapEdge[],
  originId: string,
  destId: string,
  topK: number,
  _algorithm: string = "xgboost"
): RouteResult[] {
  const adj = getAdjacencyList(nodes, edges);

  const results: { nodes: string[]; time: number }[] = [];

  // Optimized MinHeap for Dijkstra
  class MinHeap {
    heap: { id: string; dist: number }[] = [];
    push(id: string, dist: number) {
      this.heap.push({ id, dist });
      let idx = this.heap.length - 1;
      while (idx > 0) {
        const pIdx = Math.floor((idx - 1) / 2);
        if (this.heap[pIdx].dist <= this.heap[idx].dist) break;
        const tmp = this.heap[pIdx];
        this.heap[pIdx] = this.heap[idx];
        this.heap[idx] = tmp;
        idx = pIdx;
      }
    }
    pop() {
      if (this.heap.length === 0) return null;
      const min = this.heap[0];
      const last = this.heap.pop()!;
      if (this.heap.length > 0) {
        this.heap[0] = last;
        let idx = 0;
        const len = this.heap.length;
        while (true) {
          let left = idx * 2 + 1;
          let right = idx * 2 + 2;
          let swap: number | null = null;
          if (left < len && this.heap[left].dist < this.heap[idx].dist) swap = left;
          if (
            right < len &&
            this.heap[right].dist < (swap === null ? this.heap[idx].dist : this.heap[left].dist)
          ) {
            swap = right;
          }
          if (swap === null) break;
          const tmp = this.heap[swap];
          this.heap[swap] = this.heap[idx];
          this.heap[idx] = tmp;
          idx = swap;
        }
      }
      return min;
    }
  }

  // Yen's K-shortest paths (simplified)
  const dijkstra = (
    blocked: Set<string>
  ): { path: string[]; cost: number } | null => {
    const dist: Record<string, number> = {};
    const prev: Record<string, string | null> = {};
    const visited = new Set<string>();

    for (const n of nodes) dist[n.id] = Infinity;
    if (!(originId in dist) || !(destId in dist)) return null;
    
    dist[originId] = 0;
    prev[originId] = null;

    const pq = new MinHeap();
    pq.push(originId, 0);

    while (pq.heap.length > 0) {
      const minEl = pq.pop();
      if (!minEl) break;
      const u = minEl.id;

      if (blocked.has(u) && u !== originId && u !== destId) continue;
      if (visited.has(u)) continue;
      visited.add(u);
      
      if (u === destId) break; // Reached goal optimally

      for (const neighbor of adj[u] || []) {
        if (blocked.has(`${u}-${neighbor.to}`)) continue;
        const alt = dist[u] + neighbor.weight;
        if (alt < dist[neighbor.to]) {
          dist[neighbor.to] = alt;
          prev[neighbor.to] = u;
          pq.push(neighbor.to, alt);
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
    } else {
      break; // No more alternative paths exist
    }
  }

  return results.map((r) => {
    const segments: RouteSegment[] = [];
    for (let j = 0; j < r.nodes.length - 1; j++) {
      const from = r.nodes[j];
      const to = r.nodes[j + 1];
      const edge = adj[from]?.find((x) => x.to === to);
      const time = edge ? edge.weight : 2.5;
      
      let traffic: "clear" | "moderate" | "heavy" = "clear";
      if (time >= 3.0) traffic = "heavy";
      else if (time >= 2.0) traffic = "moderate";

      segments.push({
        from,
        to,
        time: Math.round(time * 10) / 10,
        traffic
      });
    }

    const exactDistance = segments.reduce((sum, seg) => sum + Math.max(0.01, seg.time - 0.5), 0);

    return {
      nodes: r.nodes,
      time: Math.round(r.time * 10) / 10,
      distance: Math.round(exactDistance * 10) / 10,
      segments
    };
  });
}
