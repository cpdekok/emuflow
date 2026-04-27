import type { DeviceListItem } from "@/lib/api";

export interface DistributionEntry {
  key: string;
  count: number;
  pct: number;
}

export interface TelemetryAggregations {
  total: number;
  online: number;
  offline: number;
  shizukuPct: number;
  rootedPct: number;
  androidVersions: DistributionEntry[];
  chipsets: DistributionEntry[];
  socVendors: DistributionEntry[];
  controllerLayouts: DistributionEntry[];
  thermalStates: DistributionEntry[];
  pageSizes: DistributionEntry[];
  vendorShellCount: number;
  withVendorShellsPct: number;
  /** Average battery across reporting devices */
  avgBattery: number | null;
  /** Average battery temp */
  avgBatteryTempC: number | null;
  /** Number of save events in the last 24h, summed */
  totalSaves24h: number;
  /** Total backup failures last 24h */
  totalBackupFailures24h: number;
  /** Total vault size MB */
  totalVaultMb: number;
  /** Average heartbeat lag in seconds (now − last_seen) */
  avgHeartbeatLagSec: number | null;
}

function distribution(
  devices: DeviceListItem[],
  pick: (d: DeviceListItem) => string | null,
): DistributionEntry[] {
  const counts = new Map<string, number>();
  for (const d of devices) {
    const key = pick(d) ?? "—";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const total = devices.length || 1;
  return Array.from(counts.entries())
    .map(([key, count]) => ({
      key,
      count,
      pct: Math.round((count / total) * 1000) / 10,
    }))
    .sort((a, b) => b.count - a.count);
}

export function aggregate(devices: DeviceListItem[]): TelemetryAggregations {
  const total = devices.length;
  const online = devices.filter((d) => d.online).length;
  const shizuku = devices.filter((d) => d.shizuku_available).length;
  const rooted = devices.filter((d) => d.is_rooted).length;
  const withVendor = devices.filter(
    (d) => (d.vendor_shell_packages?.length ?? 0) > 0,
  ).length;
  const vendorPkgTotal = devices.reduce(
    (s, d) => s + (d.vendor_shell_packages?.length ?? 0),
    0,
  );

  const batteries = devices
    .map((d) => d.battery_level)
    .filter((v): v is number => v != null);
  const battTemps = devices
    .map((d) => d.battery_temperature_c)
    .filter((v): v is number => v != null);

  const lags: number[] = [];
  const now = Date.now();
  for (const d of devices) {
    const ts = new Date(d.last_seen).getTime();
    if (!Number.isNaN(ts)) lags.push(Math.max(0, (now - ts) / 1000));
  }

  const totalSaves24h = devices.reduce(
    (s, d) => s + (d.save_events_24h?.saves_total ?? 0),
    0,
  );
  const totalBackupFailures24h = devices.reduce(
    (s, d) => s + (d.save_events_24h?.backup_failures_24h ?? 0),
    0,
  );
  const totalVaultMb = devices.reduce(
    (s, d) => s + (d.save_events_24h?.vault_size_mb ?? 0),
    0,
  );

  const pct = (n: number) => (total ? Math.round((n / total) * 1000) / 10 : 0);
  const avg = (xs: number[]) =>
    xs.length ? Math.round((xs.reduce((s, x) => s + x, 0) / xs.length) * 10) / 10 : null;

  return {
    total,
    online,
    offline: total - online,
    shizukuPct: pct(shizuku),
    rootedPct: pct(rooted),
    androidVersions: distribution(devices, (d) =>
      d.android_release ? `Android ${d.android_release}` : `API ${d.android_api}`,
    ),
    chipsets: distribution(devices, (d) => d.chipset),
    socVendors: distribution(devices, (d) => d.soc_vendor),
    controllerLayouts: distribution(devices, (d) => {
      if (d.controller_layout === "dual_stick") return "Dual sticks";
      if (d.controller_layout === "single_stick") return "Single stick";
      if (d.controller_layout === "no_stick") return "Geen sticks";
      return "Onbekend";
    }),
    thermalStates: distribution(devices, (d) => d.thermal_state),
    pageSizes: distribution(devices, (d) =>
      d.page_size ? `${d.page_size / 1024} KB` : null,
    ),
    vendorShellCount: vendorPkgTotal,
    withVendorShellsPct: pct(withVendor),
    avgBattery: avg(batteries),
    avgBatteryTempC: avg(battTemps),
    totalSaves24h,
    totalBackupFailures24h,
    totalVaultMb,
    avgHeartbeatLagSec: avg(lags),
  };
}
