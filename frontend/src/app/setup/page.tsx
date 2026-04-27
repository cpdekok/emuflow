"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowPathIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  RocketLaunchIcon,
  ShieldCheckIcon,
  TrashIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import { api, ApiError, type DeviceListItem } from "@/lib/api";
import {
  runPreflightChecks,
  summary,
  type CheckResult,
  type CheckSeverity,
} from "@/components/setup/preflightChecks";

type Step = "device" | "preflight" | "clean-slate" | "review";

interface CleanSlateChoice {
  /** "A" = vendor shells aan laten (default), "B" = uitschakelen */
  vendorMode: "A" | "B";
  /** Welke specifieke pakketten te disablen als mode = B */
  disabledPackages: Set<string>;
  /** Verwijder oude emulator-installaties die EmuFlow niet beheert */
  removeOrphans: boolean;
}

const DEFAULT_CHOICE: CleanSlateChoice = {
  vendorMode: "A",
  disabledPackages: new Set(),
  removeOrphans: false,
};

export default function SetupPage() {
  const [devices, setDevices] = useState<DeviceListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState<Step>("device");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [choice, setChoice] = useState<CleanSlateChoice>(DEFAULT_CHOICE);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await api.listDevices();
        if (cancelled) return;
        list.sort((a, b) => a.device_name.localeCompare(b.device_name));
        setDevices(list);
        if (list.length === 1) setSelectedId(list[0].device_id);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? `Backend antwoordt niet (HTTP ${err.status})`
            : err instanceof Error
              ? err.message
              : "Onbekende fout",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => devices?.find((d) => d.device_id === selectedId) ?? null,
    [devices, selectedId],
  );

  const checks = useMemo<CheckResult[]>(
    () => (selected ? runPreflightChecks(selected) : []),
    [selected],
  );
  const sum = useMemo(() => summary(checks), [checks]);

  const stepIndex: Record<Step, number> = {
    device: 0,
    preflight: 1,
    "clean-slate": 2,
    review: 3,
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Setup wizard
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Pre-flight checks en clean-slate voorbereiding voor je handheld.
        </p>
      </div>

      {/* Stepper */}
      <Stepper current={stepIndex[step]} />

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {/* Step content */}
      {step === "device" && (
        <DeviceStep
          devices={devices}
          loading={loading}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onNext={() => setStep("preflight")}
        />
      )}

      {step === "preflight" && selected && (
        <PreflightStep
          device={selected}
          checks={checks}
          onBack={() => setStep("device")}
          onNext={() => setStep("clean-slate")}
          blocked={sum.blocking}
        />
      )}

      {step === "clean-slate" && selected && (
        <CleanSlateStep
          device={selected}
          choice={choice}
          onChange={setChoice}
          onBack={() => setStep("preflight")}
          onNext={() => setStep("review")}
        />
      )}

      {step === "review" && selected && (
        <ReviewStep
          device={selected}
          checks={checks}
          choice={choice}
          onBack={() => setStep("clean-slate")}
        />
      )}
    </div>
  );
}

/* ─────────────────────────── Stepper ─────────────────────────── */

const STEPS: { key: Step; label: string }[] = [
  { key: "device", label: "Device" },
  { key: "preflight", label: "Pre-flight" },
  { key: "clean-slate", label: "Clean-slate" },
  { key: "review", label: "Plan" },
];

function Stepper({ current }: { current: number }) {
  return (
    <ol className="flex items-center gap-2 flex-wrap">
      {STEPS.map((s, i) => {
        const isActive = i === current;
        const isDone = i < current;
        return (
          <li key={s.key} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                isActive
                  ? "bg-violet-600 text-white border-violet-500"
                  : isDone
                    ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                    : "bg-slate-800 text-slate-400 border-slate-700/50"
              }`}
            >
              <span className="w-5 h-5 rounded-full bg-black/20 flex items-center justify-center text-[10px]">
                {i + 1}
              </span>
              {s.label}
            </div>
            {i < STEPS.length - 1 && (
              <ChevronRightIcon className="w-4 h-4 text-slate-600" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

/* ─────────────────────────── Step 1: Device ─────────────────────────── */

function DeviceStep({
  devices,
  loading,
  selectedId,
  onSelect,
  onNext,
}: {
  devices: DeviceListItem[] | null;
  loading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onNext: () => void;
}) {
  if (loading) {
    return (
      <Card>
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <ArrowPathIcon className="w-4 h-4 animate-spin" />
          Devices ophalen…
        </div>
      </Card>
    );
  }

  if (!devices || devices.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-300">
          Nog geen devices gekoppeld. Installeer eerst de EmuFlow Agent op je
          handheld; daarna verschijnt het apparaat hier vanzelf.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-white">
        Welke handheld wil je voorbereiden?
      </h2>
      <p className="text-sm text-slate-400 mt-1">
        Selecteer het apparaat waarop je emulators wilt installeren.
      </p>
      <div className="mt-4 space-y-2">
        {devices.map((d) => {
          const active = d.device_id === selectedId;
          return (
            <button
              key={d.device_id}
              type="button"
              onClick={() => onSelect(d.device_id)}
              className={`w-full text-left p-4 rounded-lg border transition-colors ${
                active
                  ? "bg-violet-600/10 border-violet-500/40"
                  : "bg-slate-900/40 border-slate-700/50 hover:border-slate-600"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {d.device_name}
                  </p>
                  <p className="text-xs text-slate-400 truncate">
                    {d.chipset} • Android {d.android_release ?? "?"} • {d.ram_gb}{" "}
                    GB RAM
                  </p>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-md border ${
                    d.online
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                      : "text-slate-500 bg-slate-700/30 border-slate-600/30"
                  }`}
                >
                  {d.online ? "Online" : "Offline"}
                </span>
              </div>
            </button>
          );
        })}
      </div>
      <FlowButtons onNext={onNext} nextDisabled={!selectedId} />
    </Card>
  );
}

/* ─────────────────────────── Step 2: Pre-flight ─────────────────────────── */

function PreflightStep({
  device,
  checks,
  onBack,
  onNext,
  blocked,
}: {
  device: DeviceListItem;
  checks: CheckResult[];
  onBack: () => void;
  onNext: () => void;
  blocked: boolean;
}) {
  return (
    <Card>
      <h2 className="text-lg font-semibold text-white">
        Pre-flight checks — {device.device_name}
      </h2>
      <p className="text-sm text-slate-400 mt-1">
        Op basis van de laatste heartbeat van het apparaat.
      </p>
      <ul className="mt-4 space-y-2">
        {checks.map((c) => (
          <li
            key={c.id}
            className="bg-slate-900/40 border border-slate-700/50 rounded-lg p-3"
          >
            <div className="flex items-start gap-3">
              <SeverityIcon severity={c.severity} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{c.label}</p>
                <p className="text-xs text-slate-400 mt-0.5">{c.detail}</p>
                {c.remediation && (
                  <p className="text-xs text-amber-300/80 mt-1">
                    → {c.remediation}
                  </p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
      {blocked && (
        <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-start gap-2">
          <XCircleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-300">
            Eén of meer blokkerende checks: los die eerst op voor je doorgaat.
          </p>
        </div>
      )}
      <FlowButtons
        onBack={onBack}
        onNext={onNext}
        nextDisabled={blocked}
        nextLabel="Door naar clean-slate"
      />
    </Card>
  );
}

function SeverityIcon({ severity }: { severity: CheckSeverity }) {
  if (severity === "ok")
    return <CheckCircleIcon className="w-5 h-5 text-emerald-400 flex-shrink-0" />;
  if (severity === "warn")
    return (
      <ExclamationTriangleIcon className="w-5 h-5 text-amber-400 flex-shrink-0" />
    );
  if (severity === "fail")
    return <XCircleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />;
  return <InformationCircleIcon className="w-5 h-5 text-slate-500 flex-shrink-0" />;
}

/* ─────────────────────────── Step 3: Clean-slate ─────────────────────────── */

function CleanSlateStep({
  device,
  choice,
  onChange,
  onBack,
  onNext,
}: {
  device: DeviceListItem;
  choice: CleanSlateChoice;
  onChange: (c: CleanSlateChoice) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const vendorPkgs = device.vendor_shell_packages ?? [];

  const togglePackage = (pkg: string) => {
    const next = new Set(choice.disabledPackages);
    if (next.has(pkg)) next.delete(pkg);
    else next.add(pkg);
    onChange({ ...choice, disabledPackages: next });
  };

  return (
    <Card>
      <h2 className="text-lg font-semibold text-white">
        Clean-slate — {device.device_name}
      </h2>
      <p className="text-sm text-slate-400 mt-1">
        Bepaal hoe EmuFlow met fabrikant-specifieke software omgaat. Default A
        laat alles staan en is veilig — kies B alleen als je weet wat je doet.
      </p>

      {/* Mode A */}
      <RadioOption
        active={choice.vendorMode === "A"}
        onClick={() =>
          onChange({ ...choice, vendorMode: "A", disabledPackages: new Set() })
        }
        title="A — Vendor-shells laten staan (aanbevolen)"
        description="EmuFlow installeert eigen emulators naast de fabrikant-launcher. Garantie en OTA-updates blijven werken. Default."
      />

      {/* Mode B */}
      <RadioOption
        active={choice.vendorMode === "B"}
        onClick={() => onChange({ ...choice, vendorMode: "B" })}
        title="B — Vendor-shells uitschakelen"
        description="Selecteer specifieke pakketten om uit te schakelen via Shizuku. Apparaat blijft bruikbaar maar fabrikant-functies (Aya Space, Master Controller, etc.) verdwijnen tot je ze weer activeert."
      />

      {choice.vendorMode === "B" && (
        <div className="mt-3 ml-8 bg-slate-900/40 border border-slate-700/50 rounded-lg p-3 space-y-2">
          <p className="text-xs text-slate-400">
            Aanwezige vendor-pakketten ({vendorPkgs.length}):
          </p>
          {vendorPkgs.length === 0 ? (
            <p className="text-xs text-slate-500 italic">Geen aangetroffen.</p>
          ) : (
            vendorPkgs.map((pkg) => (
              <label
                key={pkg}
                className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer hover:text-white"
              >
                <input
                  type="checkbox"
                  checked={choice.disabledPackages.has(pkg)}
                  onChange={() => togglePackage(pkg)}
                  className="rounded border-slate-600 bg-slate-800 text-violet-500 focus:ring-violet-500/30"
                />
                <code className="font-mono">{pkg}</code>
              </label>
            ))
          )}
        </div>
      )}

      {/* Orphan removal */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={choice.removeOrphans}
            onChange={(e) =>
              onChange({ ...choice, removeOrphans: e.target.checked })
            }
            className="mt-0.5 rounded border-slate-600 bg-slate-800 text-violet-500 focus:ring-violet-500/30"
          />
          <div>
            <p className="text-sm font-medium text-white">
              Bestaande losse emulator-installaties verwijderen
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Zoekt naar handmatig geïnstalleerde versies van emulators die
              EmuFlow ook beheert (bijv. een oude Citra-APK), en biedt aan die
              te de-installeren zodat versie-conflicten worden voorkomen.
              Configuraties en saves blijven behouden.
            </p>
          </div>
        </label>
      </div>

      <FlowButtons onBack={onBack} onNext={onNext} nextLabel="Naar plan" />
    </Card>
  );
}

function RadioOption({
  active,
  onClick,
  title,
  description,
}: {
  active: boolean;
  onClick: () => void;
  title: string;
  description: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left mt-3 p-4 rounded-lg border transition-colors ${
        active
          ? "bg-violet-600/10 border-violet-500/40"
          : "bg-slate-900/40 border-slate-700/50 hover:border-slate-600"
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-1 w-4 h-4 rounded-full border-2 flex-shrink-0 ${
            active
              ? "border-violet-400 bg-violet-500"
              : "border-slate-500 bg-transparent"
          }`}
        />
        <div>
          <p className="text-sm font-semibold text-white">{title}</p>
          <p className="text-xs text-slate-400 mt-1">{description}</p>
        </div>
      </div>
    </button>
  );
}

/* ─────────────────────────── Step 4: Review ─────────────────────────── */

function ReviewStep({
  device,
  checks,
  choice,
  onBack,
}: {
  device: DeviceListItem;
  checks: CheckResult[];
  choice: CleanSlateChoice;
  onBack: () => void;
}) {
  const sum = summary(checks);

  return (
    <Card>
      <h2 className="text-lg font-semibold text-white">Installatieplan</h2>
      <p className="text-sm text-slate-400 mt-1">
        Controleer en bevestig. EmuFlow voert dit straks uit op je handheld.
      </p>

      <div className="mt-4 space-y-4">
        <Block
          icon={ShieldCheckIcon}
          title="Apparaat"
          rows={[
            { label: "Naam", value: device.device_name },
            { label: "Chipset", value: device.chipset },
            {
              label: "Android",
              value: `${device.android_release ?? "?"} (API ${device.android_api})`,
            },
            { label: "RAM", value: `${device.ram_gb} GB` },
            {
              label: "Page size",
              value: device.page_size
                ? `${device.page_size / 1024} KB`
                : "—",
            },
          ]}
        />
        <Block
          icon={CheckCircleIcon}
          title="Pre-flight"
          rows={[
            { label: "OK", value: String(sum.ok) },
            { label: "Waarschuwingen", value: String(sum.warn) },
            { label: "Geblokkeerd", value: String(sum.fail) },
          ]}
        />
        <Block
          icon={TrashIcon}
          title="Clean-slate"
          rows={[
            {
              label: "Modus",
              value:
                choice.vendorMode === "A"
                  ? "A — vendor-shells laten staan (default)"
                  : "B — vendor-shells uitschakelen",
            },
            {
              label: "Uit te schakelen",
              value:
                choice.disabledPackages.size === 0
                  ? "geen"
                  : `${choice.disabledPackages.size} pakket(ten)`,
            },
            {
              label: "Orphans verwijderen",
              value: choice.removeOrphans ? "ja" : "nee",
            },
          ]}
        />
      </div>

      <div className="mt-6 bg-slate-900/40 border border-slate-700/50 rounded-lg p-4 flex items-start gap-3">
        <InformationCircleIcon className="w-5 h-5 text-violet-300 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-slate-300">
          De feitelijke uitvoering (clean-slate, emulator-install,
          permission-bundel) draait pas in een volgende fase op de Agent. Voor
          nu wordt dit plan vastgelegd voor handmatige verificatie tijdens de
          eerste end-to-end testrun.
        </p>
      </div>

      <FlowButtons
        onBack={onBack}
        onNext={() => alert("Plan bevestigd. Uitvoering volgt op het apparaat.")}
        nextLabel="Plan bevestigen"
        nextIcon={RocketLaunchIcon}
      />
    </Card>
  );
}

/* ─────────────────────────── Helpers ─────────────────────────── */

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-800 rounded-xl border border-slate-700/50 p-5">
      {children}
    </div>
  );
}

function Block({
  icon: Icon,
  title,
  rows,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  rows: { label: string; value: string }[];
}) {
  return (
    <div className="bg-slate-900/40 border border-slate-700/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-violet-300" />
        <p className="text-sm font-semibold text-white">{title}</p>
      </div>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {rows.map((r) => (
          <div key={r.label} className="flex justify-between gap-2">
            <dt className="text-slate-500">{r.label}</dt>
            <dd className="text-slate-200 text-right">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function FlowButtons({
  onBack,
  onNext,
  nextDisabled,
  nextLabel = "Volgende",
  nextIcon: NextIcon,
}: {
  onBack?: () => void;
  onNext: () => void;
  nextDisabled?: boolean;
  nextLabel?: string;
  nextIcon?: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="mt-6 flex items-center justify-between gap-3">
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="px-4 py-2 text-sm text-slate-300 hover:text-white"
        >
          Terug
        </button>
      ) : (
        <span />
      )}
      <button
        type="button"
        onClick={onNext}
        disabled={nextDisabled}
        className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
      >
        {NextIcon && <NextIcon className="w-4 h-4" />}
        {nextLabel}
      </button>
    </div>
  );
}
