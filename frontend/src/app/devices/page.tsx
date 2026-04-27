"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  DevicePhoneMobileIcon,
  ExclamationTriangleIcon,
  QrCodeIcon,
  WrenchScrewdriverIcon,
} from "@heroicons/react/24/outline";
import { api, ApiError, type DeviceListItem } from "@/lib/api";
import { DeviceCard } from "@/components/devices/DeviceCard";

const setupSteps = [
  {
    icon: ArrowDownTrayIcon,
    step: "1",
    title: "Shizuku installeren",
    description:
      "Installeer Shizuku via Google Play of GitHub en activeer het via ADB of Wireless debugging.",
  },
  {
    icon: WrenchScrewdriverIcon,
    step: "2",
    title: "EmuFlow Agent APK installeren",
    description:
      "Download en installeer de EmuFlow Agent APK op je Android apparaat. Geef de vereiste machtigingen.",
  },
  {
    icon: QrCodeIcon,
    step: "3",
    title: "QR code scannen",
    description:
      "Open de EmuFlow Agent app en scan de QR code die hier verschijnt om je device te koppelen.",
  },
];

const REFRESH_INTERVAL_MS = 15_000;

export default function DevicesPage() {
  const [devices, setDevices] = useState<DeviceListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshedAt, setRefreshedAt] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const list = await api.listDevices();
      list.sort((a, b) => a.device_name.localeCompare(b.device_name));
      setDevices(list);
      setError(null);
      setRefreshedAt(Date.now());
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? `Backend antwoordt niet (HTTP ${err.status})`
          : err instanceof Error
            ? err.message
            : "Onbekende fout";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(load, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const onlineCount = devices?.filter((d) => d.online).length ?? 0;
  const total = devices?.length ?? 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Devices
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Beheer gekoppelde Android-apparaten.{" "}
            {refreshedAt && (
              <span className="text-slate-500">
                Live data, ververst elke 15s.
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={load}
            className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/50 text-slate-300 text-sm font-medium rounded-lg transition-colors duration-150"
            title="Nu verversen"
          >
            <ArrowPathIcon
              className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
            />
            Verversen
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors duration-150"
          >
            <DevicePhoneMobileIcon className="w-4 h-4" />
            Device koppelen
          </button>
        </div>
      </div>

      {/* Stats strip */}
      {devices && devices.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatPill label="Totaal" value={String(total)} />
          <StatPill
            label="Online"
            value={String(onlineCount)}
            tone="emerald"
          />
          <StatPill
            label="Offline"
            value={String(total - onlineCount)}
            tone={total - onlineCount > 0 ? "slate" : "slate"}
          />
          <StatPill
            label="Met Shizuku"
            value={String(
              devices.filter((d) => d.shizuku_available).length,
            )}
            tone="violet"
          />
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-300">
              Kan devices niet ophalen
            </p>
            <p className="text-xs text-red-400/80 mt-1 break-all">{error}</p>
          </div>
          <button
            type="button"
            onClick={load}
            className="text-xs text-red-300 hover:text-red-200 underline flex-shrink-0"
          >
            Opnieuw proberen
          </button>
        </div>
      )}

      {/* Live device cards */}
      {devices && devices.length > 0 ? (
        <div>
          <h2 className="text-lg font-semibold text-white mb-3">
            Gekoppelde devices
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {devices.map((d) => (
              <DeviceCard key={d.device_id} device={d} />
            ))}
          </div>
        </div>
      ) : (
        <>
          {/* Setup steps shown when geen devices */}
          <div>
            <h2 className="text-lg font-semibold text-white mb-3">
              Zo koppel je een device
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {setupSteps.map(({ icon: Icon, step, title, description }) => (
                <div
                  key={step}
                  className="bg-slate-800 rounded-xl p-5 border border-slate-700/50 space-y-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-full bg-violet-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                      {step}
                    </span>
                    <Icon className="w-5 h-5 text-violet-400" />
                  </div>
                  <h3 className="text-sm font-semibold text-white">{title}</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-3">
              Gekoppelde devices
            </h2>
            <div className="bg-slate-800 rounded-xl border border-slate-700/50 overflow-hidden">
              <div className="px-4 py-16 text-center">
                <div className="flex flex-col items-center gap-3">
                  <DevicePhoneMobileIcon className="w-10 h-10 text-slate-600" />
                  <p className="text-slate-400 text-sm font-medium">
                    {loading
                      ? "Devices ophalen..."
                      : "Nog geen devices gekoppeld"}
                  </p>
                  <p className="text-slate-600 text-xs">
                    Volg de stappen hierboven om je eerste device te koppelen.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatPill({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: string;
  tone?: "emerald" | "slate" | "violet";
}) {
  const toneMap: Record<string, string> = {
    emerald: "text-emerald-400",
    slate: "text-slate-200",
    violet: "text-violet-300",
  };
  return (
    <div className="bg-slate-800 border border-slate-700/50 rounded-xl px-4 py-3">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className={`text-2xl font-bold mt-1 ${toneMap[tone]}`}>{value}</p>
    </div>
  );
}
