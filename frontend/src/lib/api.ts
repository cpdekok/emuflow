/**
 * EmuFlow API client.
 *
 * Centralised wrapper around the Railway backend so every page hits the
 * same base URL and uses the same fetch defaults.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://backend-production-05dd.up.railway.app";

export type ControllerLayout = "dual_stick" | "single_stick" | "no_stick";

export interface SaveEvents24h {
  saves_total: number;
  saves_per_emulator: Record<string, number>;
  vault_size_mb: number;
  vault_versions_total: number;
  backup_failures_24h: number;
}

export interface DeviceListItem {
  device_id: string;
  device_name: string;
  chipset: string;
  android_api: number;
  ram_gb: number;
  shizuku_available: boolean;
  agent_version: string | null;
  last_seen: string;
  online: boolean;
  manufacturer: string | null;
  model: string | null;
  android_release: string | null;
  soc_vendor: string | null;
  soc_chip: string | null;
  gpu_family: string | null;
  page_size: number | null;
  ram_mb: number | null;
  shizuku_version: number | null;
  is_rooted: boolean;
  has_analog_sticks: boolean | null;
  controller_layout: ControllerLayout | null;
  vendor_shell_packages: string[] | null;
  thermal_state: string | null;
  battery_level: number | null;
  battery_temperature_c: number | null;
  last_heartbeat_at: string | null;
  save_events_24h: SaveEvents24h | null;
}

export interface CrashEvent {
  id: string;
  device_id: string;
  timestamp: string;
  emulator_package: string | null;
  game_id: string | null;
  platform: string | null;
  crash_reason: string | null;
  crash_signal: string | null;
  created_at: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let body = "";
    try {
      body = await res.text();
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, `${res.status} ${res.statusText}: ${body}`);
  }
  return (await res.json()) as T;
}

export interface LibraryStats {
  device_id: string;
  total_count: number;
  by_platform: Record<string, number>;
  preinstalled_count: number;
  duplicate_groups_exact: number;
  duplicate_groups_probable: number;
  language_candidates: number;
  scan_completed_at: string | null;
  reported_at: string;
}

export interface LauncherInfo {
  package_name: string;
  display_name: string;
  is_default_home: boolean;
  is_installed: boolean;
  boxart_capability: "auto" | "manual" | "none";
  video_capability: "auto" | "manual" | "none";
  notes: string | null;
}

export interface LauncherReport {
  device_id: string;
  detected: LauncherInfo[];
  active_home_package: string | null;
  detected_at: string | null;
  reported_at: string;
}

export const api = {
  listDevices: () => request<DeviceListItem[]>("/devices"),
  getDeviceEvents: (deviceId: string, limit = 25) =>
    request<{ events: unknown[] }>(
      `/devices/${encodeURIComponent(deviceId)}/events?limit=${limit}`,
    ),
  getDeviceLibrary: (deviceId: string) =>
    request<LibraryStats>(`/devices/${encodeURIComponent(deviceId)}/library`),
  getDeviceLaunchers: (deviceId: string) =>
    request<LauncherReport>(`/devices/${encodeURIComponent(deviceId)}/launchers`),
  health: () => request<{ status: string; version: string }>("/health"),
};
