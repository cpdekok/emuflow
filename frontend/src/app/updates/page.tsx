"use client";

import { useState } from "react";
import {
  ArrowPathIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";

type StatusType = "unknown" | "current" | "outdated";

interface Emulator {
  name: string;
  category: "frontend" | "standalone" | "tool";
  latestVersion: string | null;
  status: StatusType;
}

const initialEmulators: Emulator[] = [
  {
    name: "RetroArch",
    category: "frontend",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "Dolphin",
    category: "standalone",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "PPSSPP",
    category: "standalone",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "NetherSX2",
    category: "standalone",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "Lime3DS",
    category: "standalone",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "ES-DE",
    category: "frontend",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "Obtainium",
    category: "tool",
    latestVersion: null,
    status: "unknown",
  },
  {
    name: "Sudachi",
    category: "standalone",
    latestVersion: null,
    status: "unknown",
  },
];

const categoryLabel: Record<string, string> = {
  frontend: "Frontend",
  standalone: "Standalone",
  tool: "Tool",
};

const categoryColor: Record<string, string> = {
  frontend: "bg-blue-900/40 text-blue-300",
  standalone: "bg-violet-900/40 text-violet-300",
  tool: "bg-emerald-900/40 text-emerald-300",
};

function StatusBadge({ status }: { status: StatusType }) {
  if (status === "current") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-900/40 text-emerald-400">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
        Actueel
      </span>
    );
  }
  if (status === "outdated") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-900/40 text-amber-400">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
        Update beschikbaar
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700/60 text-slate-400">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-500 inline-block" />
      Onbekend
    </span>
  );
}

export default function UpdatesPage() {
  const [emulators] = useState<Emulator[]>(initialEmulators);
  const [checking, setChecking] = useState(false);

  const handleCheck = async () => {
    setChecking(true);
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    try {
      await fetch(`${apiUrl}/updates/check`);
    } catch {
      // API not yet available — handled gracefully
    } finally {
      setTimeout(() => setChecking(false), 1200);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Emulator Updates
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Bekijk de updatestatus van ondersteunde emulatoren.
          </p>
        </div>
        <button
          type="button"
          onClick={handleCheck}
          disabled={checking}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-violet-800 disabled:cursor-wait text-white text-sm font-medium rounded-lg transition-colors duration-150"
        >
          <ArrowPathIcon
            className={`w-4 h-4 ${checking ? "animate-spin" : ""}`}
          />
          {checking ? "Checken…" : "Check nu"}
        </button>
      </div>

      {/* Emulators Table */}
      <div className="bg-slate-800 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Emulator
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Categorie
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Laatste versie
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {emulators.map((emulator) => (
                <tr
                  key={emulator.name}
                  className="hover:bg-slate-700/30 transition-colors duration-100"
                >
                  <td className="px-4 py-3 font-medium text-white">
                    {emulator.name}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        categoryColor[emulator.category]
                      }`}
                    >
                      {categoryLabel[emulator.category]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">
                    {emulator.latestVersion ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={emulator.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Obtainium Export */}
      <div className="flex justify-end">
        <button
          type="button"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition-colors duration-150"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          Obtainium Export
        </button>
      </div>
    </div>
  );
}
