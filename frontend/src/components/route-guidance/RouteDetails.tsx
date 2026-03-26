import { motion } from "framer-motion";
import { ArrowRight, Clock, X } from "lucide-react";
import type { AlgorithmId, RouteResult } from "./cityMapData";
import { TrafficBadge } from "./TrafficBadge";

interface RouteDetailsProps {
  route: RouteResult;
  index: number;
  algorithm: AlgorithmId;
  onClose: () => void;
}

export function RouteDetails({ route, index, algorithm, onClose }: RouteDetailsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 12 }}
      className="bg-white rounded-[24px] p-6 border border-slate-200/60 shadow-sm space-y-5"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-[15px] font-bold text-slate-800">
            {index === 0 ? "Optimal Route" : `Alternative ${index}`} - Segment Breakdown
          </h3>
          <p className="text-[13px] text-slate-500 font-medium mt-1">
            Predicted by <span className="uppercase font-semibold">{algorithm}</span> model
          </p>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors shadow-sm"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-0 pt-2 pb-2">
        {route.segments.map((segment, segmentIndex) => (
          <div key={`${segment.from}-${segment.to}-${segmentIndex}`} className="flex items-stretch gap-4">
            <div className="flex flex-col items-center w-4 mt-1">
              <div
                className={`w-3 h-3 rounded-full shrink-0 shadow-sm border border-white ${
                  segment.traffic === "clear"
                    ? "bg-emerald-500"
                    : segment.traffic === "moderate"
                      ? "bg-amber-500"
                      : "bg-red-500"
                }`}
              />
              {segmentIndex < route.segments.length - 1 && <div className="w-0.5 flex-1 bg-slate-100 my-1" />}
            </div>

            <div className="flex-1 pb-4 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="text-[13px] font-bold text-slate-700">{segment.from}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
                <span className="text-[13px] font-bold text-slate-700">{segment.to}</span>
              </div>
              <div className="flex items-center gap-3">
                <TrafficBadge level={segment.traffic} />
                <span className="flex items-center gap-1.5 text-[13px] font-medium text-slate-500 w-16 justify-end">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {segment.time} min
                </span>
              </div>
            </div>
          </div>
        ))}

        <div className="flex items-center gap-4">
          <div className="flex flex-col items-center w-4 mt-1">
            <div className="w-3 h-3 rounded-full bg-blue-500 shrink-0 shadow-sm border border-white" />
          </div>
          <span className="text-[13px] font-bold text-slate-700">{route.nodes[route.nodes.length - 1]}</span>
        </div>
      </div>
    </motion.div>
  );
}
