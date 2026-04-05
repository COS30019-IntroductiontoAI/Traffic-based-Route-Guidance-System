import { useEffect, useMemo, useRef, useState } from "react";
import type { DataKey, MapNode, RouteResult } from "@/components/route-guidance/cityMapData";

type LatLng = [number, number];
type LngLat = [number, number];

interface UseRoadGeometriesParams {
  routes: RouteResult[];
  nodes: MapNode[];
  dataKey: DataKey;
  selectedRoute: number;
}

interface UseRoadGeometriesResult {
  routeGeometries: Record<number, LatLng[]>;
  isFetchingGeometry: boolean;
}

interface OsrmRouteGeometry {
  coordinates?: Array<[number, number]>;
}

interface OsrmResponse {
  code?: string;
  routes?: Array<{ geometry?: OsrmRouteGeometry }>;
}

const OSRM_ROUTE_API = "https://router.project-osrm.org/route/v1/driving";
const MAX_WAYPOINTS_PER_REQUEST = 60;
const MAX_GEOMETRY_CACHE_ENTRIES = 500;

const geometryCache = new Map<string, LatLng[]>();
const inFlightGeometryRequests = new Map<string, Promise<LatLng[] | null>>();

function buildRouteKey(dataKey: DataKey, route: RouteResult): string {
  return `${dataKey}:${route.nodes.join(">")}`;
}

function readRouteNodes(route: RouteResult, nodeLookup: Map<string, MapNode>): LatLng[] {
  return route.nodes
    .map((nodeId) => nodeLookup.get(nodeId))
    .filter((node): node is MapNode => Boolean(node))
    .map((node) => [node.lat, node.lng]);
}

function toLngLat(points: LatLng[]): LngLat[] {
  return points.map(([lat, lng]) => [lng, lat]);
}

function toLatLng(points: Array<[number, number]>): LatLng[] {
  return points
    .map(([lng, lat]) => [lat, lng] as LatLng)
    .filter(([lat, lng]) => Number.isFinite(lat) && Number.isFinite(lng));
}

function appendUniqueLatLng(base: LatLng[], incoming: LatLng[]): LatLng[] {
  if (base.length === 0) {
    return [...incoming];
  }

  const merged = [...base];
  for (const point of incoming) {
    const last = merged[merged.length - 1];
    if (!last || last[0] !== point[0] || last[1] !== point[1]) {
      merged.push(point);
    }
  }
  return merged;
}

function setGeometryCache(routeKey: string, geometry: LatLng[]): void {
  if (!geometry.length) {
    return;
  }

  if (geometryCache.size >= MAX_GEOMETRY_CACHE_ENTRIES) {
    const firstInsertedKey = geometryCache.keys().next().value;
    if (firstInsertedKey) {
      geometryCache.delete(firstInsertedKey);
    }
  }
  geometryCache.set(routeKey, geometry);
}

async function requestOsrmChunk(waypoints: LngLat[], signal: AbortSignal): Promise<LatLng[] | null> {
  if (waypoints.length < 2) {
    return null;
  }

  const encoded = waypoints.map(([lng, lat]) => `${lng.toFixed(6)},${lat.toFixed(6)}`).join(";");
  const url = `${OSRM_ROUTE_API}/${encoded}?overview=simplified&geometries=geojson&steps=false&alternatives=false&continue_straight=true`;

  const response = await fetch(url, { signal });
  if (!response.ok) {
    return null;
  }

  const payload = (await response.json()) as OsrmResponse;
  if (payload.code !== "Ok") {
    return null;
  }

  const coordinates = payload.routes?.[0]?.geometry?.coordinates;
  if (!coordinates || coordinates.length < 2) {
    return null;
  }

  const latLng = toLatLng(coordinates);
  return latLng.length >= 2 ? latLng : null;
}

async function fetchRoadGeometry(waypoints: LngLat[], signal: AbortSignal): Promise<LatLng[] | null> {
  if (waypoints.length < 2) {
    return null;
  }

  if (waypoints.length <= MAX_WAYPOINTS_PER_REQUEST) {
    return requestOsrmChunk(waypoints, signal);
  }

  let merged: LatLng[] = [];
  for (let index = 0; index < waypoints.length - 1; index += MAX_WAYPOINTS_PER_REQUEST - 1) {
    const chunk = waypoints.slice(index, index + MAX_WAYPOINTS_PER_REQUEST);
    if (chunk.length < 2) {
      continue;
    }

    const chunkGeometry = await requestOsrmChunk(chunk, signal);
    if (!chunkGeometry) {
      return null;
    }

    merged = appendUniqueLatLng(merged, chunkGeometry);
  }

  return merged.length >= 2 ? merged : null;
}

async function getRoadGeometry(routeKey: string, waypoints: LngLat[], signal: AbortSignal): Promise<LatLng[] | null> {
  const cached = geometryCache.get(routeKey);
  if (cached) {
    return cached;
  }

  const inFlight = inFlightGeometryRequests.get(routeKey);
  if (inFlight) {
    return inFlight;
  }

  const requestPromise = fetchRoadGeometry(waypoints, signal)
    .then((geometry) => {
      if (geometry) {
        setGeometryCache(routeKey, geometry);
      }
      return geometry;
    })
    .catch(() => {
      return null;
    })
    .finally(() => {
      inFlightGeometryRequests.delete(routeKey);
    });

  inFlightGeometryRequests.set(routeKey, requestPromise);
  return requestPromise;
}

export function useRoadGeometries({
  routes,
  nodes,
  dataKey,
  selectedRoute,
}: UseRoadGeometriesParams): UseRoadGeometriesResult {
  const [routeGeometries, setRouteGeometries] = useState<Record<number, LatLng[]>>({});
  const [isFetchingGeometry, setIsFetchingGeometry] = useState(false);
  const requestSequenceRef = useRef(0);

  const nodeLookup = useMemo(() => {
    return new Map(nodes.map((node) => [node.id, node]));
  }, [nodes]);

  useEffect(() => {
    const requestId = ++requestSequenceRef.current;
    const abortController = new AbortController();

    if (!routes.length || !nodes.length) {
      setRouteGeometries({});
      setIsFetchingGeometry(false);
      return () => {
        abortController.abort();
      };
    }

    const seeded: Record<number, LatLng[]> = {};
    const missingIndices: number[] = [];

    routes.forEach((route, index) => {
      const routeKey = buildRouteKey(dataKey, route);
      const cachedGeometry = geometryCache.get(routeKey);
      if (cachedGeometry && cachedGeometry.length >= 2) {
        seeded[index] = cachedGeometry;
      } else {
        missingIndices.push(index);
      }
    });

    setRouteGeometries(seeded);

    if (!missingIndices.length) {
      setIsFetchingGeometry(false);
      return () => {
        abortController.abort();
      };
    }

    setIsFetchingGeometry(true);

    const prioritized = [
      ...missingIndices.filter((index) => index === selectedRoute),
      ...missingIndices.filter((index) => index !== selectedRoute),
    ];

    const fetchAndStore = async (routeIndex: number): Promise<void> => {
      const route = routes[routeIndex];
      if (!route) {
        return;
      }

      const latLngWaypoints = readRouteNodes(route, nodeLookup);
      if (latLngWaypoints.length < 2) {
        return;
      }

      const routeKey = buildRouteKey(dataKey, route);
      const geometry = await getRoadGeometry(routeKey, toLngLat(latLngWaypoints), abortController.signal);

      if (!geometry || abortController.signal.aborted || requestId !== requestSequenceRef.current) {
        return;
      }

      setRouteGeometries((previous) => {
        if (previous[routeIndex]) {
          return previous;
        }
        return {
          ...previous,
          [routeIndex]: geometry,
        };
      });
    };

    void (async () => {
      const [firstPriority, ...remaining] = prioritized;
      if (firstPriority !== undefined) {
        await fetchAndStore(firstPriority);
      }

      await Promise.all(remaining.map((routeIndex) => fetchAndStore(routeIndex)));

      if (!abortController.signal.aborted && requestId === requestSequenceRef.current) {
        setIsFetchingGeometry(false);
      }
    })();

    return () => {
      abortController.abort();
    };
  }, [dataKey, nodeLookup, nodes.length, routes, selectedRoute]);

  return {
    routeGeometries,
    isFetchingGeometry,
  };
}
