import React from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color?: "violet" | "blue" | "green" | "amber";
}

const colorMap = {
  violet: {
    iconBg: "bg-violet-600/20",
    iconText: "text-violet-400",
  },
  blue: {
    iconBg: "bg-blue-600/20",
    iconText: "text-blue-400",
  },
  green: {
    iconBg: "bg-emerald-600/20",
    iconText: "text-emerald-400",
  },
  amber: {
    iconBg: "bg-amber-600/20",
    iconText: "text-amber-400",
  },
};

export default function StatCard({
  title,
  value,
  label,
  icon: Icon,
  color = "violet",
}: StatCardProps) {
  const colors = colorMap[color];

  return (
    <div className="bg-slate-800 rounded-xl p-5 flex items-center gap-4 border border-slate-700/50 hover:border-slate-600/60 transition-colors duration-150">
      {/* Icon */}
      <div
        className={`flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${colors.iconBg}`}
      >
        <Icon className={`w-6 h-6 ${colors.iconText}`} />
      </div>

      {/* Text */}
      <div className="min-w-0">
        <p className="text-slate-400 text-xs font-medium uppercase tracking-wider truncate">
          {title}
        </p>
        <p className="text-2xl font-bold text-white mt-0.5 leading-none">
          {value}
        </p>
        <p className="text-slate-500 text-xs mt-1 truncate">{label}</p>
      </div>
    </div>
  );
}
