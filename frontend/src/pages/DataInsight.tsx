import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, LineChart, Line, ComposedChart,
} from "recharts";
import {
  CalendarDays, MapPin, Activity, LoaderCircle, ServerCrash, Target, BarChart3,
} from "lucide-react";

import rhythmData from "../../data/json/1_LineChart_Traffic_By_Hour.json";
import weekdayData from "../../data/json/2_BarChart_Weekday_Vs_Weekend.json";
import hotspotsData from "../../data/json/3_MapChart_Traffic_Hotspots_LatLng.json";
import boxPlotData from "../../data/json/4_BoxPlot_Volume_Distribution_By_Hour.json";
import dayOfWeekData from "../../data/json/5_BarChart_DayOfWeek_Traffic.json";

// Framer Motion animation config
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] as const } },
};

// Generic tooltip for all charts
const CustomTooltip = ({ active, payload, label, unit }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-lg font-sans">
        <p className="text-slate-700 font-semibold mb-1 border-b border-slate-100 pb-1">{label}</p>
        {payload.map((p: any, index: number) => (
          <p key={index} className="text-sm font-medium mt-1" style={{ color: p.color || p.fill || p.stroke }}>
            {p.name}: {p.value.toLocaleString()} {unit || "veh/h"}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Custom dot that labels the two peak hours (8 AM and 5 PM)
const PeakDot = (props: any) => {
  const { cx, cy, value, payload } = props;

  if (payload.hour !== 8 && payload.hour !== 17) return null;

  return (
    <g>
      <circle cx={cx} cy={cy} r={6} stroke="#2563eb" strokeWidth={3} fill="#ffffff" />
      <rect x={cx - 24} y={cy - 32} width={48} height={22} fill="#1e293b" rx={4} />
      <text x={cx} y={cy - 16} fill="#ffffff" fontSize={11} fontWeight="bold" textAnchor="middle">
        {value}
      </text>
    </g>
  );
};

// Reusable card wrapper: renders a chart with an insight summary below
const InsightPanel = ({ icon, title, text, children, className, heightClass = "h-[260px]" }: any) => (
  <motion.div variants={item} className={`bg-white rounded-[24px] border border-slate-200/60 p-6 shadow-sm flex flex-col ${className}`}>
    <div className="flex items-center gap-2 mb-2">
      {icon}
      <h2 className="font-semibold text-gray-900">{title}</h2>
    </div>
    <div className={`${heightClass} mb-5 mt-2`}>
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100/70 mt-auto">
      <p className="text-[13px] text-slate-600 leading-relaxed font-medium">
        <span className="font-bold text-slate-800">Insight:</span> {text}
      </p>
    </div>
  </motion.div>
);

export default function DataInsights() {
  const [data, setData] = useState<any>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const fetchAllData = async () => {
      try {
        setIsLoading(true);

        // Fetch a single JSON file from the storytelling API
        const fetchJson = async (fileName: string) => {
          const res = await fetch(
            `http://127.0.0.1:8000/api/storytelling?file=${fileName}`,
            { signal: abortController.signal }
          );
          if (!res.ok) throw new Error(`Failed to load ${fileName}`);
          return res.json();
        };

        // Fetch all 5 chart datasets in parallel
        const [rhythm, weekday, hotspots, boxPlot, dayOfWeek] = await Promise.all([
          fetchJson("1_LineChart_Traffic_By_Hour.json"),
          fetchJson("2_BarChart_Weekday_Vs_Weekend.json"),
          fetchJson("3_MapChart_Traffic_Hotspots_LatLng.json"),
          fetchJson("4_BoxPlot_Volume_Distribution_By_Hour.json"),
          fetchJson("5_BarChart_DayOfWeek_Traffic.json"),
        ]);

        setData({
          rhythm,
          weekdayWeekend: weekday,
          hotspotsHoriz: hotspots.slice(0, 10).map((i: any) => ({
            name: `SCATS ${i.scats_number}`,
            volume: i.traffic_volume,
            location: i.location,
          })),
          boxPlot: boxPlot.map((item: any) => ({ ...item, x: item.hour })),
          dayOfWeek,
        });
      } catch (err: any) {
        if (!abortController.signal.aborted) {
          setData({
            rhythm: rhythmData,
            weekdayWeekend: weekdayData,
            hotspotsHoriz: hotspotsData.slice(0, 10).map((i: any) => ({
              name: `SCATS ${i.scats_number}`,
              volume: i.traffic_volume,
              location: i.location,
            })),
            boxPlot: boxPlotData.map((item: any) => ({ ...item, x: item.hour })),
            dayOfWeek: dayOfWeekData,
          });
          setError(null);
        }
      } finally {
        if (!abortController.signal.aborted) setIsLoading(false);
      }
    };

    fetchAllData();
    return () => abortController.abort();
  }, []);

  if (isLoading) return (
    <div className="flex h-full min-h-[80vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4 text-slate-500">
        <LoaderCircle className="w-8 h-8 animate-spin text-blue-500" />
        <p className="text-sm font-medium">Extracting core insights from backend...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="flex h-full min-h-[80vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-center max-w-sm">
        <ServerCrash className="w-8 h-8 text-red-400" />
        <p className="text-sm font-semibold text-slate-700">Could not load storytelling data</p>
        <p className="text-xs text-slate-400">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="p-8 max-w-[1500px] w-full min-h-screen font-sans">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">

        {/* Header */}
        <motion.div variants={item}>
          <h1 className="text-[26px] font-bold tracking-tight text-slate-800">
            High-Value Traffic Insights
          </h1>
          <p className="text-[14px] text-slate-500 font-medium mt-1">
            Refined Exploratory Data Analysis (EDA) on the SCATS 2006 Dataset. Focused strictly on temporal rhythms and spatial bottlenecks.
          </p>
        </motion.div>

        {/* Chart 1 — Full-width overview: hourly volume vs average baseline (composed chart) */}
        <InsightPanel
          // icon={<Activity size={20} className="text-blue-500" />}
          title="Hourly Traffic Rhythm vs Average Baseline"
          heightClass="h-[350px]"
          text="The red dashed line marks the overall average (103.9 veh/h). Two critical spikes appear at 8 AM (173.6) and 5 PM (194.4). Route Guidance weights should penalise these windows most heavily."
        >
          <ComposedChart data={data.rhythm} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="pulseColor" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip unit="veh/h" />} />
            <Legend wrapperStyle={{ fontSize: '13px', paddingTop: '15px', fontWeight: 500 }} />
            <Area type="monotone" dataKey="traffic_volume" name="Hourly Volume" stroke="#3b82f6" strokeWidth={3} fill="url(#pulseColor)" />
            <Line type="monotone" dataKey="traffic_volume" stroke="transparent" dot={<PeakDot />} activeDot={false} legendType="none" tooltipType="none" />
            <Line type="step" dataKey="overall_average" name="Overall Avg Baseline (103.9)" stroke="#ef4444" strokeWidth={2} strokeDasharray="6 6" dot={false} />
          </ComposedChart>
        </InsightPanel>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          <InsightPanel
            // icon={<CalendarDays size={18} className="text-indigo-500" />}
            title="Weekday vs Weekend Dynamics"
            text="Weekdays show two sharp peaks at 8 AM and 5 PM. Weekend traffic is smoother, with a moderate peak around midday and no strong spikes."
          >
            <BarChart data={data.weekdayWeekend} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="weekday_volume" name="Weekday" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="weekend_volume" name="Weekend" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </InsightPanel>

          <InsightPanel
            // icon={<BarChart3 size={18} className="text-violet-500" />}
            title="Traffic Flow by Day of Week"
            text="Friday has the highest volume, while Sunday is the lowest. Clear weekly pattern for prediction."
          >
            <BarChart data={data.dayOfWeek} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="day_name" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fontSize: 11, fill: '#9ca3af' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
              <Bar dataKey="traffic_volume" name="Avg Volume" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={40} />
            </BarChart>
          </InsightPanel>

          <InsightPanel
            // icon={<MapPin size={18} className="text-rose-500" />}
            title="Top 10 Bottlenecks"
            text="SCATS 3685 is the busiest. Hotspots cluster around Warrigal Rd, forming key bottlenecks."
          >
            <BarChart data={data.hotspotsHoriz} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#4b5563', fontWeight: 500 }} axisLine={false} tickLine={false} width={80} />
              <Tooltip
                contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }}
                formatter={(value: any, name: any, props: any) => [`${value.toLocaleString()} vehicles`, props.payload.location]}
              />
              <Bar dataKey="volume" name="Volume" fill="#f43f5e" radius={[0, 4, 4, 0]} barSize={14} />
            </BarChart>
          </InsightPanel>

          <InsightPanel
            // icon={<Target size={18} className="text-orange-500" />}
            title="Volume Variance (IQR and Outliers)"
            text="Median rises during peak hours, with wider IQR indicating higher variability during the day."
          >
            <LineChart data={data.boxPlot} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} domain={['dataMin', 'dataMax']} />
              <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Line type="monotone" dataKey="median" name="Median" stroke="#ea580c" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="q1" name="Q1" stroke="#ea580c" strokeDasharray="5 5" strokeWidth={1} dot={false} />
              <Line type="monotone" dataKey="q3" name="Q3" stroke="#ea580c" strokeDasharray="5 5" strokeWidth={1} dot={false} />
            </LineChart>
          </InsightPanel>

        </div>

      </motion.div>
    </div>
  );
}