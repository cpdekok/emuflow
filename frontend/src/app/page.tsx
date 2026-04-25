import StatCard from "@/components/StatCard";
import {
  DevicePhoneMobileIcon,
  CpuChipIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  PlusCircleIcon,
  RocketLaunchIcon,
  CloudArrowUpIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          EmuFlow Dashboard
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Beheer je emulatie-setup vanuit één plek — automatisch gedeployed via GitHub.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="Devices"
          value="—"
          label="Gekoppelde apparaten"
          icon={DevicePhoneMobileIcon}
          color="violet"
        />
        <StatCard
          title="Emulatoren"
          value="8"
          label="Ondersteunde emulatoren"
          icon={CpuChipIcon}
          color="blue"
        />
        <StatCard
          title="Updates"
          value="—"
          label="Beschikbare updates"
          icon={ArrowPathIcon}
          color="amber"
        />
        <StatCard
          title="BIOS"
          value="—"
          label="Geverifieerde BIOS"
          icon={ShieldCheckIcon}
          color="green"
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">
          Snelle acties
        </h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/devices"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors duration-150"
          >
            <PlusCircleIcon className="w-4 h-4" />
            Nieuw device koppelen
          </Link>
          <Link
            href="/updates"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition-colors duration-150"
          >
            <ArrowPathIcon className="w-4 h-4" />
            Updates checken
          </Link>
          <button
            type="button"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-medium rounded-lg transition-colors duration-150"
          >
            <CloudArrowUpIcon className="w-4 h-4" />
            Config deployen
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">
          Recente activiteit
        </h2>
        <div className="bg-slate-800 rounded-xl border border-slate-700/50 p-8 flex flex-col items-center justify-center gap-3 text-center min-h-[160px]">
          <RocketLaunchIcon className="w-10 h-10 text-slate-600" />
          <p className="text-slate-400 text-sm font-medium">
            Nog geen activiteit
          </p>
          <p className="text-slate-600 text-xs max-w-xs">
            Koppel een device of voer een actie uit om activiteit te zien.
          </p>
        </div>
      </div>
    </div>
  );
}
