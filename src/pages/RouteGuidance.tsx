import React, { useState } from 'react'
import { Clock, Milestone, CheckCircle } from 'lucide-react'
import { useApp } from '../App'

interface Route {
  label: string
  score: number
  time: number
  distance: number
  nodes: string[]
  color: string
}

// Simple SVG grid map
const NODES: Record<string, { x: number; y: number }> = {
  '4021': { x: 80, y: 280 },
  '4035': { x: 80, y: 160 },
  '4051': { x: 200, y: 160 },
  '4063': { x: 200, y: 280 },
  '4078': { x: 320, y: 40 },
  '4090': { x: 200, y: 40 },
  '4031': { x: 320, y: 160 },
  '4042': { x: 440, y: 160 },
}

const EDGES = [
  ['4021', '4035'], ['4021', '4063'],
  ['4035', '4051'], ['4035', '4090'],
  ['4051', '4078'], ['4051', '4031'], ['4051', '4063'],
  ['4063', '4031'],
  ['4078', '4090'], ['4078', '4031'],
  ['4031', '4042'],
  ['4090', '4031'],
]

const MapView = ({ origin, dest, routes, selectedRoute }: {
  origin: string; dest: string; routes: Route[]; selectedRoute: number
}) => {
  const route = routes[selectedRoute]
  const routeEdges: [string, string][] = route
    ? route.nodes.slice(0, -1).map((n, i) => [n, route.nodes[i + 1]])
    : []

  return (
    <svg viewBox="0 0 520 360" className="w-full h-full">
      <defs>
        <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
          <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#f1f5f9" strokeWidth="1"/>
        </pattern>
        <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto">
          <polygon points="0 0, 6 2, 0 4" fill="#6366f1" opacity="0.7" />
        </marker>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>

      {/* Grid background */}
      <rect width="520" height="360" fill="url(#grid)" />

      {/* Background edges */}
      {EDGES.map(([a, b], i) => {
        const na = NODES[a], nb = NODES[b]
        if (!na || !nb) return null
        const isRouteEdge = routeEdges.some(([ra, rb]) =>
          (ra === a && rb === b) || (ra === b && rb === a)
        )
        return (
          <g key={i}>
            {/* Shadow line for route edges */}
            {isRouteEdge && (
              <line
                x1={na.x + 12} y1={na.y + 12}
                x2={nb.x + 12} y2={nb.y + 12}
                stroke="#6366f1" strokeWidth={10} strokeLinecap="round" opacity={0.1}
              />
            )}
            <line
              x1={na.x + 12} y1={na.y + 12}
              x2={nb.x + 12} y2={nb.y + 12}
              stroke={isRouteEdge ? '#6366f1' : '#cbd5e1'}
              strokeWidth={isRouteEdge ? 3.5 : 1.5}
              strokeLinecap="round"
              strokeDasharray={isRouteEdge ? 'none' : '4 3'}
              markerEnd={isRouteEdge ? 'url(#arrowhead)' : undefined}
            />
          </g>
        )
      })}

      {/* Nodes */}
      {Object.entries(NODES).map(([id, pos]) => {
        const isOrigin = id === origin
        const isDest = id === dest
        const isOnRoute = route?.nodes.includes(id)
        const cx = pos.x + 12
        const cy = pos.y + 12
        return (
          <g key={id}>
            {/* Pulse ring for origin/dest */}
            {(isOrigin || isDest) && (
              <circle cx={cx} cy={cy} r={16}
                fill={isOrigin ? '#6366f1' : '#8b5cf6'}
                opacity={0.15}
              />
            )}
            <circle
              cx={cx} cy={cy}
              r={isOrigin || isDest ? 9 : isOnRoute ? 7 : 5}
              fill={isOrigin ? '#6366f1' : isDest ? '#8b5cf6' : isOnRoute ? '#a5b4fc' : '#e2e8f0'}
              stroke="white"
              strokeWidth={isOrigin || isDest ? 2.5 : 2}
              filter={isOrigin || isDest ? 'url(#glow)' : undefined}
            />
            {/* Node label box */}
            <rect
              x={cx - 16} y={cy + 12}
              width={32} height={14}
              rx={4}
              fill={isOnRoute ? '#eef2ff' : '#f8fafc'}
              stroke={isOnRoute ? '#c7d2fe' : '#e2e8f0'}
              strokeWidth={1}
            />
            <text x={cx} y={cy + 22} textAnchor="middle" fontSize={8.5} fontWeight="600"
              fill={isOnRoute ? '#6366f1' : '#94a3b8'} fontFamily="monospace">
              {id}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

const defaultRoutes: Route[] = [
  { label: 'Optimal Route', score: 98, time: 12, distance: 4.2, nodes: ['4021', '4035', '4051', '4078'], color: '#6366f1' },
  { label: 'Alternative 1', score: 89, time: 15, distance: 5.1, nodes: ['4021', '4063', '4051', '4078'], color: '#8b5cf6' },
  { label: 'Alternative 2', score: 82, time: 18, distance: 6.3, nodes: ['4021', '4035', '4090', '4078'], color: '#a78bfa' },
]

export default function RouteGuidance() {
  const { toast } = useApp()
  const [origin, setOrigin] = useState('4021')
  const [dest, setDest] = useState('4078')
  const [topK, setTopK] = useState(3)
  const [routes, setRoutes] = useState<Route[]>(defaultRoutes)
  const [selectedRoute, setSelectedRoute] = useState(0)
  const [loading, setLoading] = useState(false)

  const handleFind = () => {
    if (!origin.trim() || !dest.trim()) {
      toast('Please enter both origin and destination nodes', 'error')
      return
    }
    if (origin.trim() === dest.trim()) {
      toast('Origin and destination must be different nodes', 'error')
      return
    }
    setLoading(true)
    toast(`Searching top-${topK} routes from ${origin} → ${dest}...`, 'info')
    setTimeout(() => {
      setRoutes(defaultRoutes.slice(0, topK))
      setSelectedRoute(0)
      setLoading(false)
      toast(`Found ${Math.min(topK, defaultRoutes.length)} routes. Optimal: 12 min, 4.2 km`, 'success')
    }, 900)
  }

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Route Guidance</h1>
        <p className="text-sm text-gray-400 mt-1">Find optimal travel routes between intersections.</p>
      </div>

      <div className="flex gap-4 items-start">
        {/* Left panel */}
        <div className="w-72 flex-shrink-0 space-y-4">
          {/* Input card */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
            <div className="flex gap-3">
              <div className="flex flex-col items-center gap-1 pt-6">
                <div className="w-3 h-3 rounded-full bg-indigo-600"></div>
                <div className="w-0.5 h-8 bg-indigo-200"></div>
                <div className="w-3 h-3 rounded-full bg-violet-500"></div>
              </div>
              <div className="flex-1 space-y-3">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Origin (SCATS Node)</label>
                  <input
                    type="text"
                    value={origin}
                    onChange={e => setOrigin(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Destination (SCATS Node)</label>
                  <input
                    type="text"
                    value={dest}
                    onChange={e => setDest(e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  />
                </div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-xs text-gray-500">Top-K Routes</label>
                <span className="text-xs font-semibold text-gray-800">{topK}</span>
              </div>
              <input type="range" min={1} max={5} value={topK} onChange={e => setTopK(+e.target.value)} />
            </div>

            <button
              onClick={handleFind}
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {loading ? 'Finding...' : 'Find Routes'}
            </button>
          </div>

          {/* Route cards */}
          {routes.map((route, i) => (
            <div
              key={i}
              onClick={() => setSelectedRoute(i)}
              className={`bg-white rounded-2xl border-2 p-4 cursor-pointer transition-all ${
                selectedRoute === i ? 'border-indigo-300 shadow-md shadow-indigo-50' : 'border-gray-100 hover:border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-900">{route.label}</span>
                <div className="flex items-center gap-1 text-green-600">
                  <CheckCircle size={13} />
                  <span className="text-xs font-bold">{route.score}%</span>
                </div>
              </div>
              <div className="flex gap-3 mb-3">
                <span className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock size={12} /> {route.time} min
                </span>
                <span className="flex items-center gap-1 text-xs text-gray-500">
                  <Milestone size={12} /> {route.distance} km
                </span>
              </div>
              <div className="flex items-center gap-1 flex-wrap">
                {route.nodes.map((node, ni) => (
                  <React.Fragment key={ni}>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-md font-mono">{node}</span>
                    {ni < route.nodes.length - 1 && <span className="text-gray-300 text-xs">→</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Map */}
        <div className="flex-1 bg-white rounded-2xl border border-gray-100 p-4">
          <div className="h-80">
            <MapView origin={origin} dest={dest} routes={routes} selectedRoute={selectedRoute} />
          </div>
          <div className="flex gap-4 mt-2 px-2">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-indigo-600"></div>
              <span className="text-xs text-gray-500">Origin</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-violet-500"></div>
              <span className="text-xs text-gray-500">Destination</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
