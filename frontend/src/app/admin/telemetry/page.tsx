"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowPathIcon,
  CpuChipIcon,
  DevicePhoneMobileIcon,
  ExclamationTriangleIcon,
  FireIcon,
  ShieldCheckIcon,
  SignalIcon,
} from "@heroicons/react/24/outline";
import { api, ApiError, type DeviceListItem } from "@/lib/api";
import {
  aggregate,
  type DistributionEntry,
  type TelemetryAggregations,
} from "@/components/telemetry/aggregations";

const REFRESH_MS = 30_000;

export default function TelemetryPage() {
  const [agg, setAgg] = useState<TelemetryAggregations | null>(null);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const list = await api.listDevices();
      setDevices(list);
      setAgg(aggregate(list));
      setError(null);
      setUpdatedAt(Date.now());
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `Backend antwoordt niet (HTTP ${err.status})`
          : err instanceof Error
            ? err.message
            : "Onbekende fout",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(load, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Telemetrie
            </h1>
            <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Intern
            </span>
          </div>
          <p className="text-slate-400 mt-1 text-sm">
            Live aggregaties over alle gekoppelde devices. Ververst elke 30s.
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm font-medium rounded-lg transition-colors"
        >
          <ArrowPathIcon
            className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
          />
          Verversen
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!agg || devices.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-8 text-center">
          <DevicePhoneMobileIcon className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-slate-400 text-sm mt-3">
            Nog geen devices om te aggregeren.
          </p>
        </div>
      ) : (
        <>
          {/* KPI strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Kpi
              icon={DevicePhoneMobileIcon}
              label="Totaal devices"
              value={String(agg.total)}
            />
            <Kpi
              icon={SignalIcon}
              label="Online"
              value={`${agg.online} / ${agg.total}`}
              tone="emerald"
            />
            <Kpi
              icon={ShieldCheckIcon}
              label="Met Shizuku"
              value={`${agg.shizukuPct}%`}
              tone="violet"
            />
            <Kpi
              icon={FireIcon}
              label="Gem. heartbeat lag"
              value={
                agg.avgHeartbeatLagSec != null
                  ? `${Math.round(agg.avgHeartbeatLagSec)}s`
                  : "—"
              }
            />
          </div>

          {/* Save & crash row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Kpi
              label="Saves 24u"
              value={String(agg.totalSaves24h)}
            />
            <Kpi
              label="Vault totaal"
              value={`${agg.totalVaultMb} MB`}
            />
            <Kpi
              label="Backup fouten 24u"
              value={String(agg.totalBackupFailures24h)}
              tone={
                agg.totalBackupFailures24h > 0 ? "red" : "emerald"
              }
            />
            <Kpi
              label="Gem. batt. temp"
              value={
                agg.avgBatteryTempC != null
                  ? `${agg.avgBatteryTempC}°C`
                  : "—"
              }
              tone={
                agg.avgBatteryTempC != null && agg.avgBatteryTempC >= 40
                  ? "amber"
                  : "slate"
              }
            />
          </div>

          {/* Distribution panels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DistributionPanel
              icon={CpuChipIcon}
              title="Android-versies"
              entries={agg.androidVersions}
            />
            <DistributionPanel
              icon={CpuChipIcon}
              title="Chipsets"
              entries={agg.chipsets}
            />
            <DistributionPanel
              icon={CpuChipIcon}
              title="SoC-vendors"
              entries={agg.socVendors}
            />
            <DistributionPanel
              icon={CpuChipIcon}
              title="Controller layouts"
              entries={agg.controllerLayouts}
            />
            <DistributionPanel
              icon={FireIcon}
              title="Thermal states"
              entries={agg.thermalStates}
            />
            <DistributionPanel
              icon={CpuChipIcon}
              title="Page sizes"
              entries={agg.pageSizes}
            />
          </div>

          {/* Vendor & root callouts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Callout
              title="Vendor-shells"
              body={
                <>
                  <span className="text-2xl font-bold text-violet-300">
                    {agg.withVendorShellsPct}%
                  </span>{" "}
                  van devices heeft minimaal één vendor-pakket actief
                  (totaal: {agg.vendorShellCount} pakketten).
                </>
              }
            />
            <Callout
              title="Root status"
              body={
                <>
                  <span className="text-2xl font-bold text-amber-300">
                    {agg.rootedPct}%
                  </span>{" "}
                  van devices is rooted.
                </>
              }
            />
          </div>

          {updatedAt && (
            <p className="text-xs text-slate-500">
              Laatst bijgewerkt:{" "}
              {new Date(updatedAt).toLocaleTimeString("nl-NL")}
            </p>
          )}
        </>
      )}
    </div>
  );
}

/* ─────────────────────────── Components ─────────────────────────── */

function Kpi({
  icon: Icon,
  label,
  value,
  tone = "slate",
}: {
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  tone?: "slate" | "emerald" | "violet" | "amber" | "red";
}) {
  const toneClass: Record<string, string> = {
    slate: "text-slate-200",
    emerald: "text-emerald-400",
    violet: "text-violet-300",
    amber: "text-amber-300",
    red: "text-red-400",
  };
  return (
    <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-4">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-500">
        {Icon && <Icon className="w-3.5 h-3.5" />}
        {label}
      </div>
      <p className={`mt-1 text-2xl font-bold ${toneClass[tone]}`}>{value}</p>
    </div>
  );
}

function DistributionPanel({
  icon: Icon,
  title,
  entries,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  entries: DistributionEntry[];
}) {
  return (
    <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-violet-300" />
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <ul className="space-y-2">
        {entries.length === 0 && (
          <li className="text-xs text-slate-500 italic">Geen data.</li>
        )}
        {entries.map((e) => (
          <li key={e.key}>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300 truncate" title={e.key}>
                {e.key}
              </span>
              <span className="text-slate-400 flex-shrink-0">
                {e.count} ({e.pct}%)
              </span>
            </div>
            <div className="h-1.5 bg-slate-900/60 rounded-full overflow-hidden">
              <div
                className="h-full bg-violet-500/70 rounded-full"
                style={{ width: `${Math.max(2, e.pct)}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Callout({
  title,
  body,
}: {
  title: string;
  body: React.ReactNode;
}) {
  return (
    <div className="bg-slate-800 border border-slate-700/50 rounded-xl p-5">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <p className="text-sm text-slate-300 mt-2 leading-relaxed">{body}</p>
    </div>
  );
}
