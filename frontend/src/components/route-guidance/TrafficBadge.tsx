interface TrafficBadgeProps {
  level: "clear" | "moderate" | "heavy";
  size?: "sm" | "md";
}

// Muted, understated palette — not the vivid "AI" look
const config = {
  clear: {
    label: "Clear",
    dot: "bg-emerald-400",
    bg: "bg-slate-50",
    text: "text-slate-500",
    border: "border-slate-200",
  },
  moderate: {
    label: "Moderate",
    dot: "bg-amber-400",
    bg: "bg-slate-50",
    text: "text-slate-500",
    border: "border-slate-200",
  },
  heavy: {
    label: "Heavy",
    dot: "bg-red-400",
    bg: "bg-slate-50",
    text: "text-slate-500",
    border: "border-slate-200",
  },
};

export function TrafficBadge({ level, size = "sm" }: TrafficBadgeProps) {
  const c = config[level] ?? config.clear;
  return (
    <span
      className={`inline-flex items-center gap-1.5 ${c.bg} ${c.text} border ${c.border} rounded-full ${
        size === "sm" ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs"
      } font-medium`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}
