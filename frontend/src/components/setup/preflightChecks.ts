import type { DeviceListItem } from "@/lib/api";

export type CheckSeverity = "ok" | "warn" | "fail" | "skip";

export interface CheckResult {
  id: string;
  label: string;
  severity: CheckSeverity;
  detail: string;
  remediation?: string;
}

const KNOWN_VENDOR_PREFIXES = [
  "com.retroid.",
  "com.ayaneo.",
  "com.anbernic.",
  "com.ayn.",
];

/**
 * Run all pre-flight checks against a device's last heartbeat.
 *
 * Phase 1 minimum: Android 11+, page size 4 KB or 16 KB, Shizuku reachable,
 * battery healthy enough to flash, controllers detectable, vendor shells
 * inventoried.
 */
export function runPreflightChecks(d: DeviceListItem): CheckResult[] {
  const out: CheckResult[] = [];

  // 1. Android version
  if (d.android_api < 30) {
    out.push({
      id: "android-version",
      label: "Android-versie",
      severity: "fail",
      detail: `API ${d.android_api} (Android ${d.android_release ?? "?"}). EmuFlow vereist minimaal Android 11 (API 30).`,
      remediation:
        "Update het apparaat naar Android 11 of hoger via de fabrikant-OTA, of gebruik een andere handheld.",
    });
  } else if (d.android_api < 33) {
    out.push({
      id: "android-version",
      label: "Android-versie",
      severity: "warn",
      detail: `API ${d.android_api} (Android ${d.android_release ?? "?"}). Werkt, maar Android 13+ wordt aanbevolen voor de breedste emulator-compatibiliteit.`,
    });
  } else {
    out.push({
      id: "android-version",
      label: "Android-versie",
      severity: "ok",
      detail: `Android ${d.android_release} (API ${d.android_api}).`,
    });
  }

  // 2. Page size
  if (d.page_size == null) {
    out.push({
      id: "page-size",
      label: "Kernel page size",
      severity: "warn",
      detail:
        "Page size niet gerapporteerd. EmuFlow probeert generieke builds, maar specifieke 16 KB-builds kunnen niet automatisch geselecteerd worden.",
    });
  } else if (d.page_size === 4096 || d.page_size === 16384) {
    out.push({
      id: "page-size",
      label: "Kernel page size",
      severity: "ok",
      detail: `${d.page_size / 1024} KB pages — emulator-builds worden hierop afgestemd.`,
    });
  } else {
    out.push({
      id: "page-size",
      label: "Kernel page size",
      severity: "fail",
      detail: `Onbekende page size: ${d.page_size}. Alleen 4 KB en 16 KB worden ondersteund.`,
      remediation:
        "Controleer of het apparaat een gangbare Android-build draait. Custom kernels worden niet ondersteund.",
    });
  }

  // 3. Shizuku
  if (!d.shizuku_available) {
    out.push({
      id: "shizuku",
      label: "Shizuku",
      severity: "fail",
      detail:
        "Shizuku is niet bereikbaar. EmuFlow heeft Shizuku nodig voor stille installatie en permission-bundeling.",
      remediation:
        "Installeer Shizuku via Google Play of GitHub en activeer het via ADB / Wireless debugging. Start daarna de Agent opnieuw.",
    });
  } else {
    out.push({
      id: "shizuku",
      label: "Shizuku",
      severity: "ok",
      detail: `Shizuku v${d.shizuku_version ?? "?"} actief.`,
    });
  }

  // 4. Battery for flashing
  if (d.battery_level == null) {
    out.push({
      id: "battery",
      label: "Batterij",
      severity: "warn",
      detail: "Batterijniveau onbekend.",
    });
  } else if (d.battery_level < 25) {
    out.push({
      id: "battery",
      label: "Batterij",
      severity: "fail",
      detail: `Batterij staat op ${Math.round(d.battery_level)}%. Te laag voor veilige installatie van meerdere emulators.`,
      remediation:
        "Sluit het apparaat aan op een lader en wacht tot minimaal 50% voordat je doorgaat.",
    });
  } else if (d.battery_level < 50) {
    out.push({
      id: "battery",
      label: "Batterij",
      severity: "warn",
      detail: `Batterij op ${Math.round(d.battery_level)}%. Aansluiten op lader wordt aangeraden voor een rustige installatie.`,
    });
  } else {
    out.push({
      id: "battery",
      label: "Batterij",
      severity: "ok",
      detail: `${Math.round(d.battery_level)}% — voldoende voor installatie.`,
    });
  }

  // 5. Thermal state
  const thermal = (d.thermal_state ?? "").toUpperCase();
  if (thermal === "SEVERE" || thermal === "CRITICAL" || thermal === "EMERGENCY") {
    out.push({
      id: "thermal",
      label: "Thermal state",
      severity: "fail",
      detail: `Apparaat staat op ${thermal}. Eerst laten afkoelen voor je iets installeert.`,
      remediation: "Leg het apparaat 10 minuten weg uit direct zonlicht, sluit lopende emulators.",
    });
  } else if (thermal === "MODERATE") {
    out.push({
      id: "thermal",
      label: "Thermal state",
      severity: "warn",
      detail: "Matig warm — ok om door te gaan, maar zware emulators kunnen throttlen.",
    });
  } else if (thermal === "NORMAL" || thermal === "LIGHT") {
    out.push({
      id: "thermal",
      label: "Thermal state",
      severity: "ok",
      detail: "Apparaat op normale temperatuur.",
    });
  } else {
    out.push({
      id: "thermal",
      label: "Thermal state",
      severity: "skip",
      detail: "Niet gerapporteerd.",
    });
  }

  // 6. Storage
  if (d.android_api > 0 && d.battery_level !== null) {
    // We hebben geen vrij-storage veld in DeviceListItem; placeholder die we later vullen vanuit heartbeat
    out.push({
      id: "storage",
      label: "Vrije opslag",
      severity: "skip",
      detail:
        "Wordt gemeten zodra de Agent de eerste storage-snapshot stuurt.",
    });
  }

  // 7. Controllers
  if (d.has_analog_sticks === false) {
    out.push({
      id: "controllers",
      label: "Controllers",
      severity: "warn",
      detail:
        "Geen analoge sticks gedetecteerd (D-pad + face-buttons). PS1, N64 en analog-only games krijgen automatisch een aangepast control-profiel.",
    });
  } else if (d.has_analog_sticks === true) {
    out.push({
      id: "controllers",
      label: "Controllers",
      severity: "ok",
      detail:
        d.controller_layout === "dual_stick"
          ? "Dual analog sticks aanwezig."
          : "Analoge stick(s) aanwezig.",
    });
  } else {
    out.push({
      id: "controllers",
      label: "Controllers",
      severity: "skip",
      detail: "Layout niet gerapporteerd.",
    });
  }

  // 8. Vendor shells
  const vendorPkgs = d.vendor_shell_packages ?? [];
  const matched = vendorPkgs.filter((p) =>
    KNOWN_VENDOR_PREFIXES.some((prefix) => p.startsWith(prefix)),
  );
  if (matched.length === 0) {
    out.push({
      id: "vendor-shells",
      label: "Vendor-shells",
      severity: "ok",
      detail: "Geen bekende vendor-shells aangetroffen.",
    });
  } else {
    out.push({
      id: "vendor-shells",
      label: "Vendor-shells",
      severity: "warn",
      detail: `${matched.length} vendor-shell pakket(ten) actief: ${matched.join(", ")}. Optioneel uit te schakelen via clean-slate (default A: laten staan).`,
    });
  }

  // 9. Root
  if (d.is_rooted) {
    out.push({
      id: "root",
      label: "Root",
      severity: "warn",
      detail: "Apparaat is rooted. EmuFlow ondersteunt root, maar saves en BIOS zijn dan ook leesbaar voor andere apps.",
    });
  } else {
    out.push({
      id: "root",
      label: "Root",
      severity: "ok",
      detail: "Apparaat is niet rooted (aanbevolen).",
    });
  }

  return out;
}

export function summary(checks: CheckResult[]): {
  ok: number;
  warn: number;
  fail: number;
  skip: number;
  blocking: boolean;
} {
  const counts = { ok: 0, warn: 0, fail: 0, skip: 0 };
  for (const c of checks) counts[c.severity]++;
  return { ...counts, blocking: counts.fail > 0 };
}
