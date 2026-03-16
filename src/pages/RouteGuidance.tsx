import React, { useState } from 'react';
import { Clock, Milestone, CheckCircle } from 'lucide-react';
import { themeHex, theme } from '../theme';

interface Route {
  label: string;
  score: number;
  time: number;
  distance: number;
  nodes: string[];
}

// ─── TỌA ĐỘ SCATS MELBOURNE CHUẨN XÁC ───
const NODES: Record<string, { x: number; y: number }> = {
  '2824': { x: 215, y:  88 }, '2822': { x: 238, y:  95 }, '2821': { x: 210, y: 108 }, '2820': { x: 248, y: 103 },
  '3622': { x: 210, y: 126 }, '3007': { x: 258, y: 120 }, '3008': { x: 284, y: 112 }, '3620': { x: 243, y: 140 },
  '3621': { x: 206, y: 150 }, '2831': { x: 543, y:  62 }, '2825': { x: 549, y:  76 }, '2826': { x: 559, y:  84 },
  '2832': { x: 574, y:  52 }, '2827': { x: 597, y:  52 }, '4055': { x: 608, y:  64 }, '4054': { x: 604, y:  79 },
  '4051': { x: 558, y: 118 }, '4322': { x: 510, y: 116 }, '4052': { x: 602, y: 118 }, '4053': { x: 620, y: 118 },
  '4031': { x: 570, y: 148 }, '4032': { x: 558, y: 166 }, '4056': { x: 626, y: 180 }, '4057': { x: 643, y: 196 },
  '4058': { x: 670, y: 182 }, '4059': { x: 705, y: 200 }, '4060': { x: 712, y: 168 }, '3800': { x: 716, y: 185 },
  '3827': { x: 692, y: 116 }, '3181': { x: 718, y: 120 }, '2041': { x: 706, y:  98 }, '3180': { x: 684, y: 140 },
  '3823': { x: 680, y: 202 }, '3824': { x: 643, y: 202 }, '3822': { x: 706, y: 224 }, '2200': { x: 718, y: 202 },
  '4336': { x: 260, y: 150 }, '4339': { x: 286, y: 138 }, '4321': { x: 312, y: 150 }, '4320': { x: 260, y: 164 },
  '4335': { x: 250, y: 180 }, '3661': { x: 218, y: 178 }, '3667': { x: 239, y: 178 }, '4333': { x: 283, y: 178 },
  '4033': { x: 324, y: 178 }, '3826': { x: 340, y: 170 }, '4061': { x: 365, y: 184 }, '4062': { x: 375, y: 194 },
  '3819': { x: 394, y: 188 }, '3660': { x: 193, y: 202 }, '3662': { x: 215, y: 202 }, '3663': { x: 239, y: 202 },
  '3003': { x: 257, y: 202 }, '4324': { x: 261, y: 192 }, '4325': { x: 287, y: 196 }, '4330': { x: 266, y: 208 },
  '4331': { x: 297, y: 208 }, '3004': { x: 276, y: 216 }, '3798': { x: 312, y: 202 }, '3977': { x: 326, y: 216 },
  '4065': { x: 355, y: 216 }, '4069': { x: 390, y: 212 }, '4064': { x: 414, y: 216 }, '4066': { x: 397, y: 233 },
  '4067': { x: 430, y: 232 }, '4068': { x: 458, y: 232 }, '3000': { x: 196, y: 236 }, '3002': { x: 216, y: 236 },
  '4282': { x: 202, y: 250 }, '2484': { x: 252, y: 244 }, '4284': { x: 260, y: 254 }, '4260': { x: 284, y: 246 },
  '4261': { x: 301, y: 246 }, '4037': { x: 326, y: 244 }, '3120': { x: 312, y: 258 }, '3123': { x: 350, y: 248 },
  '3127': { x: 386, y: 254 }, '3128': { x: 398, y: 254 }, '3129': { x: 429, y: 254 }, '4262': { x: 179, y: 262 },
  '4289': { x: 188, y: 276 }, '4263': { x: 203, y: 276 }, '4265': { x: 257, y: 272 }, '4266': { x: 280, y: 272 },
  '3821': { x: 305, y: 268 }, '3121': { x: 320, y: 275 }, '3837': { x: 340, y: 275 }, '3124': { x: 354, y: 275 },
  '3127b': { x: 386, y: 254 }, '3128b': { x: 398, y: 254 }, '4279': { x: 192, y: 296 }, '4268': { x: 190, y: 310 },
  '2842': { x: 216, y: 292 }, '4269': { x: 225, y: 308 }, '4274': { x: 248, y: 296 }, '4278': { x: 267, y: 304 },
  '4281': { x: 287, y: 294 }, '1031': { x: 316, y: 296 }, '3801': { x: 340, y: 290 }, '3802': { x: 362, y: 290 },
  '3799': { x: 384, y: 292 }, '3125': { x: 423, y: 292 }, '3682': { x: 465, y: 310 }, '3808': { x: 400, y: 323 },
  '3809': { x: 424, y: 326 }, '3807': { x: 383, y: 334 }, '4270': { x: 190, y: 330 }, '4275': { x: 232, y: 330 },
  '4287': { x: 258, y: 330 }, '2839': { x: 278, y: 320 }, '4039': { x: 297, y: 320 }, '3805': { x: 341, y: 318 },
  '3806': { x: 363, y: 318 }, '3914': { x: 269, y: 342 }, '4042': { x: 278, y: 352 }, '3811': { x: 302, y: 340 },
  '3829': { x: 329, y: 344 }, '4276': { x: 234, y: 358 }, '4277': { x: 262, y: 368 }, '2034': { x: 314, y: 362 },
  '3813': { x: 356, y: 370 }, '3815': { x: 362, y: 385 }, '4286': { x: 214, y: 390 }, '4283': { x: 244, y: 390 },
  '3664': { x: 270, y: 390 }, '4043': { x: 299, y: 390 }, '4044': { x: 325, y: 398 }, '2847': { x: 220, y: 424 },
  '7003': { x: 254, y: 424 }, '4045': { x: 342, y: 422 }, '4046': { x: 360, y: 422 }, '4012': { x: 374, y: 412 },
  '4049': { x: 400, y: 420 }, '1030': { x: 332, y: 452 }, '4050': { x: 400, y: 452 }, '2000': { x: 454, y: 422 },
  '3814': { x: 298, y: 486 },
};

const EDGES: [string, string][] = [
  ['2831','4051'], ['2826','4051'], ['4051','4322'], ['4051','4052'], ['4031','4032'], ['4032','3826'],
  ['2822','2820'], ['2820','3008'], ['3008','4322'], ['2824','2821'], ['2821','3622'], ['3622','3621'],
  ['3621','4336'], ['4336','4339'], ['4339','4321'], ['4321','4031'], ['4031','4052'], ['4052','4053'],
  ['3660','3662'], ['3662','3663'], ['3663','3003'], ['3003','3004'], ['3004','3798'], ['3798','3977'],
  ['3977','4065'], ['4065','4069'], ['4069','4064'], ['3661','3667'], ['3667','4335'], ['4335','4333'],
  ['4333','4033'], ['4033','3826'], ['3826','4061'], ['4061','4062'], ['4062','3819'], ['3000','3002'],
  ['3002','4282'], ['4282','2484'], ['2484','4284'], ['4284','4260'], ['4260','4261'], ['4261','4037'],
  ['4037','3120'], ['3120','3121'], ['3121','1031'], ['1031','3801'], ['3801','3802'], ['3802','3799'],
  ['4322','3826'], ['3826','3977'], ['3977','3120'], ['3120','3821'], ['3821','4039'], ['4039','3811'],
  ['3811','2034'], ['4270','4275'], ['4275','4287'], ['4287','2839'], ['2839','4039'], ['4039','3805'],
  ['3805','3806'], ['3806','3808'], ['3808','3809'], ['4335','4330'], ['4330','4284'], ['4284','4265'],
  ['4265','4274'], ['4274','4275'], ['4262','4289'], ['4289','4263'], ['4263','4282'], ['4282','4279'],
  ['4279','4270'], ['4321','4325'], ['4325','4331'], ['4331','4266'], ['4266','3821'], ['3821','2839'],
  ['2847','7003'], ['7003','4043'], ['4043','4044'], ['4044','4045'], ['4045','4046'], ['4046','4012'],
  ['4012','4049'], ['4049','4050'], ['3806','3807'], ['3807','3808'], ['4046','3815'], ['3815','3813'],
  ['4050','2000'], ['4058','4056'], ['4056','3819'], ['3819','3824'], ['3824','3823'], ['3823','2200'],
  ['4059','3800'], ['4058','4059'], ['4060','3800'], ['4053','4054'], ['4054','4055'], ['3827','2041'],
  ['3181','2041'], ['3661','3000'], ['3662','3002'], ['3663','2484'], ['4335','4324'], ['4033','4037'],
  ['3819','4069'], ['3682','3125'], ['3125','3802'], ['3806','3802'], ['4276','4283'], ['4283','7003'],
  ['4286','2847'],
];

const LABELS = [
  { x: 156, y: 202, text: 'VICTORIA PARADE',  rot: false },
  { x: 148, y: 236, text: 'VICTORIA STREET',  rot: false },
  { x: 153, y: 173, text: 'JOHNSTON STREET',  rot: false },
  { x: 430, y: 330, text: 'TOORAK ROAD',      rot: false },
  { x: 408, y: 424, text: 'MALVERN ROAD',     rot: false },
  { x: 652, y: 174, text: 'BELMORE ROAD',     rot: false },
  { x: 648, y:  88, text: 'HIGH STREET',      rot: false },
  { x: 553, y:  28, text: 'GRANGE ROAD',      rot: true  },
  { x: 168, y: 270, text: 'NICHOLSON ST',     rot: true  },
  { x: 736, y: 254, text: 'ELGAR ROAD',       rot: true  },
  { x: 748, y: 340, text: 'WARRIGAL RD',      rot: true  },
];

const defaultRoutes: Route[] = [
  { label: 'Optimal Route', score: 98, time: 12, distance: 4.2, nodes: ['3621','4336','4321','4031','4032','3826','4061'] },
  { label: 'Alternative 1', score: 89, time: 15, distance: 5.1, nodes: ['3621','3622','3003','3004','3798','3977','4065'] },
  { label: 'Alternative 2', score: 82, time: 18, distance: 6.3, nodes: ['3621','4335','4333','4033','3826','4062','3819'] },
];

const ALL_NODE_IDS = Object.keys(NODES);

import { motion, AnimatePresence } from 'framer-motion';

// ─── COMPONENT BẢN ĐỒ CỦA BẠN (Đã được làm đẹp & hoạt ảnh) ───
function MapView({ origin, dest, routes, selectedRoute }: {
  origin: string; dest: string; routes: Route[]; selectedRoute: number
}) {
  const route = routes[selectedRoute];
  const routeNodesArr = route?.nodes ?? [];
  const routeNodes = new Set<string>(routeNodesArr);

  // Create SVG path string for the route animation
  const activeRoutePathString = routeNodesArr.length > 0 
    ? `M ${routeNodesArr.map(n => NODES[n] ? `${NODES[n].x},${NODES[n].y}` : '').filter(Boolean).join(' L ')}`
    : '';

  return (
    <svg viewBox="0 0 760 510" className="w-full h-full" style={{ background: '#f8f9fa' }}>
      <defs>
        <marker id="arr" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto-start-reverse">
          <path d="M 0 0 L 6 3 L 0 6 z" fill={themeHex.primary} />
        </marker>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.15" />
        </filter>
      </defs>

      {/* Road Casings (Vẽ nền khung đường - xám nhạt) */}
      {EDGES.map(([a, b], i) => {
        const na = NODES[a], nb = NODES[b];
        if (!na || !nb) return null;
        return (
          <line key={`c${i}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="#e2e8f0" strokeWidth={8} strokeLinecap="round" />
        );
      })}

      {/* Road Fills (Lòng đường - trắng) */}
      {EDGES.map(([a, b], i) => {
        const na = NODES[a], nb = NODES[b];
        if (!na || !nb) return null;
        return (
          <line key={`f${i}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} stroke="#ffffff" strokeWidth={4} strokeLinecap="round" />
        );
      })}

      {/* Active Route Core (Vẽ đường đã chọn với animation) */}
      <AnimatePresence mode="popLayout">
        <motion.path
          key={selectedRoute + "glow"}
          d={activeRoutePathString}
          stroke={themeHex.primary}
          strokeWidth={14}
          fill="none"
          opacity={0.15}
          strokeLinejoin="round"
          strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 0.15 }}
          transition={{ duration: 1.2, ease: "easeInOut" }}
        />
        <motion.path
          key={selectedRoute + "core"}
          d={activeRoutePathString}
          stroke={themeHex.primary}
          strokeWidth={4}
          fill="none"
          strokeLinejoin="round"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.2, ease: "easeInOut" }}
        />
        <motion.path
          key={selectedRoute + "dashes"}
          d={activeRoutePathString}
          stroke="#ffffff"
          strokeWidth={1.5}
          fill="none"
          strokeDasharray="4 6"
          strokeLinejoin="round"
          strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.2, ease: "easeInOut", delay: 0.2 }}
        />
      </AnimatePresence>

      {/* Tên đường phố */}
      {LABELS.map((l, i) => (
        <text key={i} x={l.x} y={l.y} fontSize={11} fontWeight="800" fill="#94a3b8" 
          fontFamily="Inter, sans-serif" letterSpacing="1.5" textAnchor="middle" 
          transform={l.rot ? `rotate(-90,${l.x},${l.y})` : undefined}
          style={{ textShadow: '2px 2px 0 #f8f9fa, -2px -2px 0 #f8f9fa, 2px -2px 0 #f8f9fa, -2px 2px 0 #f8f9fa' }}>
          {l.text}
        </text>
      ))}

      {/* Các Node: Trạm không đặc biệt */}
      {Object.entries(NODES).map(([id, pos]) => {
        const isOrigin = id === origin;
        const actualDest = routeNodesArr.length > 0 ? routeNodesArr[routeNodesArr.length - 1] : dest;
        const isDest = id === actualDest;
        const onRoute = routeNodes.has(id);
        if (isOrigin || isDest) return null; // Render special nodes later to be on top

        return (
          <g key={id} className="group cursor-crosshair">
            <circle cx={pos.x} cy={pos.y} r={onRoute ? 4 : 2.5}
              className="transition-all duration-300 group-hover:r-[6px]"
              fill={onRoute ? themeHex.primary300 : '#cbd5e1'}
              stroke="#ffffff" strokeWidth={onRoute ? 1.5 : 1} filter="url(#shadow)"
            />
            {/* Tooltip text cho node */}
            <text x={pos.x} y={pos.y - 12} fontSize={10} fontWeight="700" textAnchor="middle" 
              fill={onRoute ? themeHex.primary : '#64748b'} 
              className={`font-mono transition-opacity duration-300 pointer-events-none ${onRoute ? 'opacity-80' : 'opacity-0 group-hover:opacity-100'}`}
              style={{ textShadow: '1px 1px 0 #fff, -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff' }}>
              {id}
            </text>
          </g>
        );
      })}

      {/* Các Node: Điểm Đi và Điểm Đến */}
      {Object.entries(NODES).map(([id, pos]) => {
        const isOrigin = id === origin;
        const actualDest = routeNodesArr.length > 0 ? routeNodesArr[routeNodesArr.length - 1] : dest;
        const isDest = id === actualDest;
        if (!isOrigin && !isDest) return null;

        return (
          <g key={id}>
            {/* Halo Effect */}
            <motion.circle 
              cx={pos.x} cy={pos.y} r={18} 
              fill={isOrigin ? themeHex.primary : themeHex.grad} 
              opacity={0.15}
              initial={{ scale: 0 }}
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            />
            {/* Core Node */}
            <circle cx={pos.x} cy={pos.y} r={7}
              fill={isOrigin ? themeHex.primary : themeHex.grad}
              stroke="#ffffff" strokeWidth={2.5} filter="url(#shadow)"
            />
            {/* Nhãn to và rõ */}
            <text x={pos.x + (pos.x > 650 ? -14 : 14)} y={pos.y + 4} 
              fontSize={12} fontWeight="800" 
              textAnchor={pos.x > 650 ? 'end' : 'start'} 
              fill={isOrigin ? themeHex.primary : themeHex.grad} 
              fontFamily="monospace"
              style={{ textShadow: '2px 2px 0 #fff, -2px -2px 0 #fff, 2px -2px 0 #fff, -2px 2px 0 #fff' }}>
              {id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── TRANG CHÍNH (PAGE COMPONENT) KHÔNG CẦN useApp ───
export default function RouteGuidance() {
  const [origin, setOrigin] = useState('3621');
  const [dest, setDest] = useState('4061');
  const [topK, setTopK] = useState(3);
  const [routes, setRoutes] = useState<Route[]>(defaultRoutes);
  const [selectedRoute, setSelectedRoute] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleFind = () => {
    if (!origin.trim() || !dest.trim()) {
      alert('Vui lòng nhập cả điểm đi và điểm đến!'); return;
    }
    if (origin.trim() === dest.trim()) {
      alert('Điểm đi và điểm đến phải khác nhau!'); return;
    }
    setLoading(true);
    setTimeout(() => {
      setRoutes(defaultRoutes.slice(0, topK));
      setSelectedRoute(0);
      setLoading(false);
    }, 900);
  };

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="mb-2">
        <h1 className="text-2xl font-bold text-gray-900">Route Guidance</h1>
        <p className="text-sm text-gray-400 mt-1">Find optimal travel routes — Melbourne SCATS network.</p>
      </div>

      <div className="flex gap-4 items-start">
        {/* PANEL TRÁI: Form điều khiển */}
        <div className="w-72 flex-shrink-0 space-y-3">
          <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4 shadow-sm">
            <div className="flex gap-3">
              <div className="flex flex-col items-center gap-1 pt-6">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: themeHex.primary }} />
                <div className="w-0.5 h-8" style={{ backgroundColor: themeHex.primary100 }} />
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: themeHex.grad }} />
              </div>
              <div className="flex-1 space-y-3">
                <div>
                  <label className="block text-xs text-gray-400 font-semibold mb-1">Origin (SCATS Node)</label>
                  <input type="text" value={origin} onChange={e => setOrigin(e.target.value)} list="rg-nodes"
                    className={`w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 ${theme.ring}`} />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 font-semibold mb-1">Destination (SCATS Node)</label>
                  <input type="text" value={dest} onChange={e => setDest(e.target.value)} list="rg-nodes"
                    className={`w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 ${theme.ring}`} />
                </div>
                <datalist id="rg-nodes">{ALL_NODE_IDS.map(n => <option key={n} value={n} />)}</datalist>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-xs text-gray-500 font-semibold">Top-K Routes</label>
                <span className="text-xs font-semibold text-gray-800">{topK}</span>
              </div>
              <input type="range" className="w-full" style={{ accentColor: themeHex.primary }} min={1} max={3} value={topK} onChange={e => setTopK(+e.target.value)} />
            </div>

            <button onClick={handleFind} disabled={loading}
              className="w-full py-2.5 rounded-xl text-white text-sm font-semibold hover:opacity-90 active:scale-95 transition-all disabled:opacity-60 shadow-md"
              style={{ background: `linear-gradient(to right, ${themeHex.primary}, ${themeHex.grad})`, boxShadow: `0 4px 12px -2px ${themeHex.primary}40` }}>
              {loading ? 'Finding...' : 'Find Routes'}
            </button>
          </div>

          {/* CÁC THẺ KẾT QUẢ ROUTE */}
          {routes.map((route, i) => (
            <div key={i} onClick={() => setSelectedRoute(i)}
              className={`bg-white rounded-2xl border-2 p-4 cursor-pointer transition-all ${
                selectedRoute === i ? 'shadow-md' : 'border-gray-100 hover:border-gray-200'
              }`}
              style={selectedRoute === i ? { borderColor: themeHex.primary300, boxShadow: `0 4px 12px -2px ${themeHex.primary}20` } : {}}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-gray-900">{route.label}</span>
                <div className="flex items-center gap-1 text-emerald-600">
                  <CheckCircle size={13} />
                  <span className="text-xs font-bold">{route.score}%</span>
                </div>
              </div>
              <div className="flex gap-3 mb-2.5">
                <span className="flex items-center gap-1 text-xs text-gray-500 font-medium"><Clock size={12} /> {route.time} min</span>
                <span className="flex items-center gap-1 text-xs text-gray-500 font-medium"><Milestone size={12} /> {route.distance} km</span>
              </div>
              <div className="flex items-center flex-wrap gap-1.5">
                {route.nodes.map((node, ni) => (
                  <React.Fragment key={ni}>
                    <span className="text-[11px] bg-slate-50 border border-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono font-medium">{node}</span>
                    {ni < route.nodes.length - 1 && <span className="text-gray-300 text-xs">→</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* PANEL PHẢI: BẢN ĐỒ */}
        <div className="flex-1 bg-white rounded-3xl border border-gray-100 overflow-hidden shadow-sm flex flex-col">
          <div className="flex-1" style={{ minHeight: 500 }}>
            {/* Component MapView nguyên bản của bạn */}
            <MapView origin={origin} dest={dest} routes={routes} selectedRoute={selectedRoute} />
          </div>
          
          {/* Huyền thoại (Legend) */}
          <div className="flex gap-6 px-6 py-4 border-t border-gray-100 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: themeHex.primary }} />
              <span className="text-xs font-semibold text-gray-500">Origin</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: themeHex.grad }} />
              <span className="text-xs font-semibold text-gray-500">Destination</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#cbd5e1]" />
              <span className="text-xs font-semibold text-gray-500">SCATS Node</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-8 rounded-full" style={{ backgroundColor: themeHex.primary }} />
              <span className="text-xs font-semibold text-gray-500">Selected Route</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}