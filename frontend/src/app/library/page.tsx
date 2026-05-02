"use client";

import { useState } from "react";
import {
  ShieldCheckIcon,
  DocumentDuplicateIcon,
  LanguageIcon,
  ArchiveBoxIcon,
  EyeSlashIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

type Tab = "preserve" | "duplicates" | "languages";

type Rom = {
  path: string;
  platform: string;
  title: string;
  size_mb: number;
  region?: string;
  language?: string;
  preinstalled: boolean;
};

type DuplicateGroup = {
  kind: "exact" | "probable";
  key: string;
  roms: Rom[];
  recommended_keep_path: string;
};

// Voorbeeld-data — in productie komt dit uit /devices/{id}/library
const PRESERVED: Rom[] = [
  { path: "/sdcard/games/download/Sonic.bin", platform: "genesis", title: "Sonic the Hedgehog", size_mb: 0.5, region: "USA", preinstalled: true },
  { path: "/sdcard/Retroid/ROMs/SNES/SuperMarioWorld.sfc", platform: "snes", title: "Super Mario World", size_mb: 0.5, region: "USA", preinstalled: true },
  { path: "/sdcard/games/download/Tetris.gb", platform: "gb", title: "Tetris", size_mb: 0.03, region: "USA", preinstalled: true },
];

const DUPLICATE_GROUPS: DuplicateGroup[] = [
  {
    kind: "exact",
    key: "sha1:abc123…",
    roms: [
      { path: "/sdcard/ROMs/SNES/Chrono Trigger (USA).sfc", platform: "snes", title: "Chrono Trigger", size_mb: 4, region: "USA", preinstalled: false },
      { path: "/sdcard/Roms/snes/Chrono Trigger.sfc", platform: "snes", title: "Chrono Trigger", size_mb: 4, region: "USA", preinstalled: false },
    ],
    recommended_keep_path: "/sdcard/Roms/snes/Chrono Trigger.sfc",
  },
  {
    kind: "probable",
    key: "snes::super mario world",
    roms: [
      { path: "/sdcard/Retroid/ROMs/SNES/SuperMarioWorld.sfc", platform: "snes", title: "Super Mario World", size_mb: 0.5, region: "USA", preinstalled: true },
      { path: "/sdcard/ROMs/SNES/Super Mario World (Europe).sfc", platform: "snes", title: "Super Mario World (Europe)", size_mb: 0.5, region: "EUR", preinstalled: false },
      { path: "/sdcard/ROMs/SNES/Super Mario World (Japan).sfc", platform: "snes", title: "Super Mario World (Japan)", size_mb: 0.5, region: "JPN", language: "Ja", preinstalled: false },
    ],
    recommended_keep_path: "/sdcard/Retroid/ROMs/SNES/SuperMarioWorld.sfc",
  },
];

const LANGUAGE_CANDIDATES: Rom[] = [
  { path: "/sdcard/ROMs/SNES/Tales of Phantasia (Japan).sfc", platform: "snes", title: "Tales of Phantasia", size_mb: 6, region: "JPN", language: "Ja", preinstalled: false },
  { path: "/sdcard/ROMs/PSX/Front Mission 3 (Japan).bin", platform: "psx", title: "Front Mission 3", size_mb: 720, region: "JPN", language: "Ja", preinstalled: false },
  { path: "/sdcard/ROMs/SNES/Mother 3 (Japan).sfc", platform: "snes", title: "Mother 3", size_mb: 32, region: "JPN", language: "Ja", preinstalled: false },
];

export default function LibraryPage() {
  const [tab, setTab] = useState<Tab>("preserve");

  const totalRoms = 423;
  const exactGroups = DUPLICATE_GROUPS.filter((g) => g.kind === "exact").length;
  const probableGroups = DUPLICATE_GROUPS.filter((g) => g.kind === "probable").length;

  return (
    <div className="p-8 space-y-6 max-w-7xl">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-white">Bibliotheek</h1>
        <p className="text-sm text-slate-400">
          Behoud preinstalled games, identificeer duplicaten en kies wat je wilt zien per taal.
          Niets wordt automatisch verwijderd.
        </p>
      </header>

      {/* KPI strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPI label="Games" value={String(totalRoms)} />
        <KPI label="Beschermd" value={String(PRESERVED.length)} accent="emerald" />
        <KPI label="Exacte duplicaten" value={String(exactGroups)} accent="amber" />
        <KPI label="Waarschijnlijke duplicaten" value={String(probableGroups)} accent="amber" />
      </div>

      {/* Trust banner */}
      <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4 flex items-start gap-3">
        <ShieldCheckIcon className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <div className="text-emerald-300 font-semibold mb-1">Preinstalled blijft staan</div>
          <p className="text-slate-300">
            ROMs die op het device aanwezig waren voordat EmuFlow werd geinstalleerd, worden
            nooit verwijderd of verplaatst — niet bij clean-slate, niet bij auto-install,
            niet bij uninstall. Zie ze hieronder onder &quot;Beschermd&quot;.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-700">
        <nav className="-mb-px flex gap-6">
          <TabButton current={tab} value="preserve" onChange={setTab} icon={ShieldCheckIcon} label="Beschermd" count={PRESERVED.length} />
          <TabButton current={tab} value="duplicates" onChange={setTab} icon={DocumentDuplicateIcon} label="Duplicaten" count={DUPLICATE_GROUPS.length} />
          <TabButton current={tab} value="languages" onChange={setTab} icon={LanguageIcon} label="Talen" count={LANGUAGE_CANDIDATES.length} />
        </nav>
      </div>

      {/* Tab content */}
      {tab === "preserve" && <PreservePanel roms={PRESERVED} />}
      {tab === "duplicates" && <DuplicatesPanel groups={DUPLICATE_GROUPS} />}
      {tab === "languages" && <LanguagesPanel roms={LANGUAGE_CANDIDATES} />}

      {/* Privacy notice */}
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4 flex items-start gap-3">
        <InformationCircleIcon className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-400 leading-relaxed">
          ROM-bestandsnamen, paden en hashes blijven volledig op je device. EmuFlow stuurt alleen
          geaggregeerde tellers (per platform, totaal duplicaten) naar de server, en alleen als
          je telemetrie hebt opt-in gezet.
        </div>
      </div>
    </div>
  );
}

function KPI({ label, value, accent }: { label: string; value: string; accent?: "emerald" | "amber" }) {
  const accentClass = accent === "emerald"
    ? "text-emerald-400"
    : accent === "amber"
    ? "text-amber-400"
    : "text-white";
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-3xl font-bold mt-1 ${accentClass}`}>{value}</div>
    </div>
  );
}

function TabButton({
  current, value, onChange, icon: Icon, label, count,
}: {
  current: Tab; value: Tab; onChange: (t: Tab) => void;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; label: string; count: number;
}) {
  const isActive = current === value;
  return (
    <button
      onClick={() => onChange(value)}
      className={`flex items-center gap-2 px-1 py-3 border-b-2 text-sm font-medium transition-colors ${
        isActive
          ? "border-violet-500 text-violet-400"
          : "border-transparent text-slate-400 hover:text-slate-200"
      }`}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-slate-800 text-slate-400">{count}</span>
    </button>
  );
}

function PreservePanel({ roms }: { roms: Rom[] }) {
  if (roms.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-8 text-center text-slate-400">
        Geen preinstalled games gedetecteerd.
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-800 text-slate-400 uppercase text-xs">
          <tr>
            <th className="px-4 py-3 text-left">Titel</th>
            <th className="px-4 py-3 text-left">Platform</th>
            <th className="px-4 py-3 text-left">Pad</th>
            <th className="px-4 py-3 text-right">Grootte</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {roms.map((rom) => (
            <tr key={rom.path}>
              <td className="px-4 py-3 text-white">{rom.title}</td>
              <td className="px-4 py-3 text-slate-400">{rom.platform.toUpperCase()}</td>
              <td className="px-4 py-3 text-slate-500 font-mono text-xs">{rom.path}</td>
              <td className="px-4 py-3 text-right text-slate-400">{formatSize(rom.size_mb)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DuplicatesPanel({ groups }: { groups: DuplicateGroup[] }) {
  if (groups.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-8 text-center text-slate-400">
        Geen duplicaten gevonden.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <DuplicateGroupCard key={group.key} group={group} />
      ))}
    </div>
  );
}

function DuplicateGroupCard({ group }: { group: DuplicateGroup }) {
  const isExact = group.kind === "exact";
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800/50 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <DocumentDuplicateIcon className={`w-4 h-4 ${isExact ? "text-amber-400" : "text-slate-400"}`} />
          <span className="text-sm font-medium text-white">
            {isExact ? "Exact identiek" : "Mogelijk dezelfde game"}
          </span>
          <span className="text-xs text-slate-500 font-mono">{group.key}</span>
        </div>
        <span className="text-xs text-slate-400">{group.roms.length} bestanden</span>
      </div>
      <div className="divide-y divide-slate-800">
        {group.roms.map((rom) => {
          const isRecommended = rom.path === group.recommended_keep_path;
          return (
            <div key={rom.path} className="flex items-center gap-3 px-4 py-3">
              {isRecommended ? (
                <CheckCircleIcon className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              ) : (
                <span className="w-5 h-5 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-white truncate">{rom.title}</span>
                  {rom.region && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{rom.region}</span>
                  )}
                  {rom.preinstalled && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300">Beschermd</span>
                  )}
                </div>
                <div className="text-xs text-slate-500 font-mono truncate">{rom.path}</div>
              </div>
              <div className="text-xs text-slate-400 flex-shrink-0">{formatSize(rom.size_mb)}</div>
            </div>
          );
        })}
      </div>
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800/30 border-t border-slate-700">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
          Aanbevolen behoud is gemarkeerd
        </div>
        <button className="text-xs px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-white transition-colors" disabled>
          Kies wat te behouden
        </button>
      </div>
    </div>
  );
}

function LanguagesPanel({ roms }: { roms: Rom[] }) {
  if (roms.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-8 text-center text-slate-400">
        Geen taal-kandidaten.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 flex items-start gap-3">
        <ExclamationTriangleIcon className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-slate-300">
          <div className="text-amber-300 font-semibold mb-1">Geen automatische verwijdering</div>
          <p>
            Onderstaande games hebben geen Engelse of Nederlandse versie op het device.
            Je kan ze verbergen in de launcher of verplaatsen naar een archief-map.
            Verwijderen kan alleen via een aparte bevestigde actie.
          </p>
        </div>
      </div>
      <div className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800 text-slate-400 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Titel</th>
              <th className="px-4 py-3 text-left">Platform</th>
              <th className="px-4 py-3 text-left">Taal</th>
              <th className="px-4 py-3 text-right">Grootte</th>
              <th className="px-4 py-3 text-right">Actie</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {roms.map((rom) => (
              <tr key={rom.path}>
                <td className="px-4 py-3 text-white">{rom.title}</td>
                <td className="px-4 py-3 text-slate-400">{rom.platform.toUpperCase()}</td>
                <td className="px-4 py-3 text-slate-400">{rom.language ?? "—"}</td>
                <td className="px-4 py-3 text-right text-slate-400">{formatSize(rom.size_mb)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex justify-end gap-1">
                    <button className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200" disabled title="Verberg in launcher">
                      <EyeSlashIcon className="w-4 h-4" />
                    </button>
                    <button className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200" disabled title="Naar archief verplaatsen">
                      <ArchiveBoxIcon className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatSize(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  if (mb >= 1) return `${mb.toFixed(0)} MB`;
  return `${(mb * 1024).toFixed(0)} KB`;
}
