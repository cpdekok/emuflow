import {
  BoltIcon,
  CpuChipIcon,
  DevicePhoneMobileIcon,
  ExclamationTriangleIcon,
  FireIcon,
  ShieldCheckIcon,
  SignalIcon,
  SignalSlashIcon,
} from "@heroicons/react/24/outline";
import type { DeviceListItem } from "@/lib/api";

interface Props {
  device: DeviceListItem;
}

function formatRelative(isoTimestamp: string): string {
  const ts = new Date(isoTimestamp).getTime();
  const diff = Date.now() - ts;
  if (Number.isNaN(diff)) return "onbekend";
  const sec = Math.max(0, Math.round(diff / 1000));
  if (sec < 60) return `${sec}s geleden`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m geleden`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}u geleden`;
  const day = Math.round(hr / 24);
  return `${day}d geleden`;
}

function thermalColor(state: string | null): string {
  switch ((state ?? "").toUpperCase()) {
    case "NORMAL":
    case "LIGHT":
      return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
    case "MODERATE":
      return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    case "SEVERE":
    case "CRITICAL":
    case "EMERGENCY":
    case "SHUTDOWN":
      return "text-red-400 bg-red-500/10 border-red-500/20";
    default:
      return "text-slate-400 bg-slate-500/10 border-slate-500/20";
  }
}

function batteryColor(pct: number | null): string {
  if (pct == null) return "text-slate-400";
  if (pct >= 60) return "text-emerald-400";
  if (pct >= 25) return "text-amber-400";
  return "text-red-400";
}

function controllerLabel(d: DeviceListItem): string {
  if (d.controller_layout === "dual_stick") return "Dual sticks";
  if (d.controller_layout === "single_stick") return "Single stick";
  if (d.controller_layout === "no_stick") return "Geen sticks (D-pad)";
  return "Onbekend";
}

export function DeviceCard({ device }: Props) {
  const battery = device.battery_level ?? null;
  const tempBattery = device.battery_temperature_c ?? null;
  const saves = device.save_events_24h;

  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700/50 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-lg bg-violet-600/20 border border-violet-500/30 flex items-center justify-center flex-shrink-0">
            <DevicePhoneMobileIcon className="w-5 h-5 text-violet-300" />
          </div>
          <div className="min-w-0">
            <h3
              className="text-base font-semibold text-white truncate"
              title={device.device_name}
            >
              {device.device_name}
            </h3>
            <p className="text-xs text-slate-400 truncate">
              {device.manufacturer ?? "—"} • {device.model ?? device.chipset}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border ${
              device.online
                ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                : "text-slate-400 bg-slate-500/10 border-slate-500/20"
            }`}
          >
            {device.online ? (
              <SignalIcon className="w-3 h-3" />
            ) : (
              <SignalSlashIcon className="w-3 h-3" />
            )}
            {device.online ? "Online" : "Offline"}
          </span>
          <span className="text-[10px] text-slate-500">
            {formatRelative(device.last_seen)}
          </span>
        </div>
      </div>

      {/* Spec grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <SpecRow icon={CpuChipIcon} label="SoC" value={device.chipset} />
        <SpecRow
          icon={CpuChipIcon}
          label="GPU"
          value={device.gpu_family ?? "—"}
        />
        <SpecRow
          icon={CpuChipIcon}
          label="Android"
          value={`${device.android_release ?? "?"} (API ${device.android_api})`}
        />
        <SpecRow
          icon={CpuChipIcon}
          label="RAM"
          value={`${device.ram_gb} GB`}
        />
        <SpecRow
          icon={CpuChipIcon}
          label="Page size"
          value={
            device.page_size ? `${device.page_size / 1024} KB` : "—"
          }
        />
        <SpecRow
          icon={CpuChipIcon}
          label="Controllers"
          value={controllerLabel(device)}
        />
      </div>

      {/* Live telemetry */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-700/50">
        <Tile
          icon={BoltIcon}
          label="Batterij"
          value={battery != null ? `${Math.round(battery)}%` : "—"}
          valueClass={batteryColor(battery)}
        />
        <Tile
          icon={FireIcon}
          label="Batt. temp"
          value={tempBattery != null ? `${tempBattery.toFixed(1)}°C` : "—"}
          valueClass={
            tempBattery != null && tempBattery >= 40
              ? "text-amber-400"
              : "text-slate-200"
          }
        />
        <Tile
          icon={FireIcon}
          label="Thermal"
          value={device.thermal_state ?? "—"}
          valueClass={thermalColor(device.thermal_state).split(" ")[0]}
        />
      </div>

      {/* Save vault stats */}
      {saves && (
        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-700/50">
          <Tile
            label="Saves 24u"
            value={String(saves.saves_total)}
            valueClass="text-slate-200"
          />
          <Tile
            label="Vault grootte"
            value={`${saves.vault_size_mb} MB`}
            valueClass="text-slate-200"
          />
          <Tile
            label="Backup fouten"
            value={String(saves.backup_failures_24h)}
            valueClass={
              saves.backup_failures_24h > 0
                ? "text-red-400"
                : "text-emerald-400"
            }
          />
        </div>
      )}

      {/* Footer: Shizuku + agent + vendor shells */}
      <div className="pt-3 border-t border-slate-700/50 flex flex-wrap items-center gap-2 text-xs">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border ${
            device.shizuku_available
              ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              : "text-slate-400 bg-slate-500/10 border-slate-500/20"
          }`}
        >
          <ShieldCheckIcon className="w-3 h-3" />
          Shizuku{" "}
          {device.shizuku_available
            ? `v${device.shizuku_version ?? "?"}`
            : "uit"}
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-slate-600/30 text-slate-400 bg-slate-700/30">
          Agent {device.agent_version ?? "?"}
        </span>
        {device.is_rooted && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-amber-500/20 text-amber-400 bg-amber-500/10">
            <ExclamationTriangleIcon className="w-3 h-3" />
            Rooted
          </span>
        )}
        {device.vendor_shell_packages &&
          device.vendor_shell_packages.length > 0 && (
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-violet-500/20 text-violet-300 bg-violet-500/10"
              title={device.vendor_shell_packages.join("\n")}
            >
              {device.vendor_shell_packages.length} vendor shell
              {device.vendor_shell_packages.length > 1 ? "s" : ""}
            </span>
          )}
      </div>
    </div>
  );
}

function SpecRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2 min-w-0">
      <Icon className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
      <span className="text-slate-500 flex-shrink-0">{label}:</span>
      <span className="text-slate-300 truncate" title={value}>
        {value}
      </span>
    </div>
  );
}

function Tile({
  icon: Icon,
  label,
  value,
  valueClass,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  valueClass: string;
}) {
  return (
    <div className="bg-slate-900/40 rounded-lg p-2.5 border border-slate-700/30">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wide text-slate-500">
        {Icon && <Icon className="w-3 h-3" />}
        {label}
      </div>
      <div className={`mt-1 text-sm font-semibold ${valueClass}`}>{value}</div>
    </div>
  );
}
