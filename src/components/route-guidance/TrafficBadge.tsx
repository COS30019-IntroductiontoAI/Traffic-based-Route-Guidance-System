interface TrafficBadgeProps {
  level: "clear" | "moderate" | "heavy";
  size?: "sm" | "md";
}

const config = {
  clear: { 
    label: "Clear", 
    dot: "bg-emerald-500", 
    bg: "bg-emerald-50", 
    text: "text-emerald-600",
    border: "border-emerald-100"
  },
  moderate: { 
    label: "Moderate", 
    dot: "bg-amber-500", 
    bg: "bg-amber-50", 
    text: "text-amber-600",
    border: "border-amber-100"
  },
  heavy: { 
    label: "Heavy", 
    dot: "bg-red-500", 
    bg: "bg-red-50", 
    text: "text-red-600",
    border: "border-red-100"
  },
};

export function TrafficBadge({ level, size = "sm" }: TrafficBadgeProps) {
  const c = config[level] ?? config.clear;
  return (
    <span className={`inline-flex items-center gap-1.5 ${c.bg} ${c.text} border ${c.border} rounded-full ${size === "sm" ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs"} font-semibold shadow-sm`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
