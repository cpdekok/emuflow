"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  HomeIcon,
  DevicePhoneMobileIcon,
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ChatBubbleLeftRightIcon,
  RocketLaunchIcon,
  ScaleIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

const navLinks = [
  { href: "/", label: "Dashboard", icon: HomeIcon },
  { href: "/devices", label: "Devices", icon: DevicePhoneMobileIcon },
  { href: "/setup", label: "Setup wizard", icon: RocketLaunchIcon },
  { href: "/controllers", label: "Controllers", icon: AdjustmentsHorizontalIcon },
  { href: "/updates", label: "Updates", icon: ArrowPathIcon },
  { href: "/bios", label: "BIOS", icon: ShieldCheckIcon },
  { href: "/support", label: "Support", icon: ChatBubbleLeftRightIcon },
  { href: "/admin/telemetry", label: "Telemetrie", icon: ChartBarIcon },
  { href: "/legal", label: "Juridisch", icon: ScaleIcon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-slate-900 border-r border-slate-700/60">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700/60">
        <span className="text-2xl leading-none">🎮</span>
        <span className="text-xl font-bold tracking-tight text-white">
          EmuFlow
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navLinks.map(({ href, label, icon: Icon }) => {
          const isActive =
            pathname != null &&
            (href === "/" ? pathname === "/" : pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                isActive
                  ? "bg-violet-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-slate-700/60">
        <p className="text-xs text-slate-500">EmuFlow v0.1.0</p>
        <p className="text-xs text-slate-600 mt-0.5">
          API:{" "}
          <span className="text-slate-500">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
          </span>
        </p>
      </div>
    </aside>
  );
}
