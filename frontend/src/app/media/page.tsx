"use client";

import {
  CheckCircleIcon,
  XCircleIcon,
  PhotoIcon,
  VideoCameraIcon,
  ArrowTopRightOnSquareIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

type LauncherCard = {
  package_name: string;
  display_name: string;
  installed: boolean;
  is_default: boolean;
  boxart_auto: boolean;
  video_auto: boolean;
  source: string;
  setup_url?: string;
  notes: string;
};

// Voorbeeld-detectie — in productie van /devices/{id}/launchers
const LAUNCHERS: LauncherCard[] = [
  {
    package_name: "com.magneticchen.daijishou",
    display_name: "Daijisho",
    installed: true,
    is_default: true,
    boxart_auto: true,
    video_auto: true,
    source: "TapiocaFox CDN, streaming",
    setup_url: "https://retrohandheldguides.com/daijisho-setup-guide/",
    notes: "Automatische boxart en gameplay-video. Geen handmatig werk.",
  },
  {
    package_name: "org.es_de.frontend",
    display_name: "ES-DE",
    installed: true,
    is_default: false,
    boxart_auto: true,
    video_auto: true,
    source: "ScreenScraper.fr (account vereist)",
    setup_url: "https://www.screenscraper.fr/",
    notes: "Volledige media-fetch via ScreenScraper-account. Quota geldt.",
  },
  {
    package_name: "org.pegasus_frontend.android",
    display_name: "Pegasus",
    installed: false,
    is_default: false,
    boxart_auto: false,
    video_auto: false,
    source: "Skraper of Skyscraper (handmatig)",
    setup_url: "https://www.skraper.net/",
    notes: "Vereist per ROM een media/<game>/boxFront.png en video.mp4. Aanbevolen: Skraper op PC.",
  },
];

const SCRAPER_TOOLS = [
  {
    name: "ScreenScraper",
    url: "https://www.screenscraper.fr/",
    description: "Community-database voor boxart, screenshots en gameplay-videos. Account vereist, quota gebaseerd.",
  },
  {
    name: "Skraper",
    url: "https://www.skraper.net/",
    description: "Desktop-tool die ScreenScraper-data ophaalt en in Daijisho/Pegasus/ES-DE-formaat exporteert.",
  },
  {
    name: "TheGamesDB",
    url: "https://thegamesdb.net/",
    description: "Open-source game database, gratis API. Beperkter aanbod dan ScreenScraper.",
  },
];

export default function MediaPage() {
  return (
    <div className="p-8 space-y-6 max-w-7xl">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-white">Boxart en gameplay-video</h1>
        <p className="text-sm text-slate-400">
          EmuFlow detecteert welke launcher je gebruikt en respecteert wat die al doet.
          We hosten zelf geen boxart of videos — we verwijzen naar de bestaande scrapers.
        </p>
      </header>

      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4 flex items-start gap-3">
        <InformationCircleIcon className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-slate-300">
          Veel Android-launchers regelen boxart en video automatisch (Daijisho, ES-DE met
          ScreenScraper-account). Voor launchers die dat niet doen, geven we hier de juiste
          tools om het zelf in te richten. Geen netwerkverkeer vanuit EmuFlow naar scrapers.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Gedetecteerde launchers</h2>
        <div className="grid gap-3">
          {LAUNCHERS.map((l) => (
            <LauncherRow key={l.package_name} launcher={l} />
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Scraper-tools</h2>
        <p className="text-sm text-slate-400">
          Voor launchers zonder ingebouwde scraper, of als je media buiten je launcher
          wilt beheren.
        </p>
        <div className="grid md:grid-cols-3 gap-3">
          {SCRAPER_TOOLS.map((tool) => (
            <a
              key={tool.url}
              href={tool.url}
              target="_blank"
              rel="noreferrer"
              className="block rounded-lg border border-slate-700 bg-slate-900 p-4 hover:border-violet-500/50 hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-white">{tool.name}</h3>
                <ArrowTopRightOnSquareIcon className="w-4 h-4 text-slate-500" />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{tool.description}</p>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

function LauncherRow({ launcher }: { launcher: LauncherCard }) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        launcher.is_default
          ? "border-violet-500/40 bg-violet-500/5"
          : launcher.installed
          ? "border-slate-700 bg-slate-900"
          : "border-slate-800 bg-slate-950 opacity-70"
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-white">{launcher.display_name}</h3>
            {launcher.is_default && (
              <span className="text-xs px-2 py-0.5 rounded bg-violet-500/20 text-violet-300">
                Actieve launcher
              </span>
            )}
            {!launcher.installed && (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                Niet geinstalleerd
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">{launcher.package_name}</p>
        </div>
        {launcher.setup_url && (
          <a
            href={launcher.setup_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-violet-400 transition-colors"
          >
            <span>Setup-gids</span>
            <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <CapabilityRow icon={PhotoIcon} label="Boxart automatisch" enabled={launcher.boxart_auto} />
        <CapabilityRow icon={VideoCameraIcon} label="Gameplay-video automatisch" enabled={launcher.video_auto} />
      </div>

      <div className="text-xs text-slate-400">
        <span className="text-slate-500">Bron:</span> {launcher.source}
      </div>
      <p className="text-xs text-slate-300 mt-2">{launcher.notes}</p>
    </div>
  );
}

function CapabilityRow({
  icon: Icon,
  label,
  enabled,
}: {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  enabled: boolean;
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className="w-4 h-4 text-slate-400" />
      <span className="text-slate-300 flex-1">{label}</span>
      {enabled ? (
        <CheckCircleIcon className="w-5 h-5 text-emerald-400" />
      ) : (
        <XCircleIcon className="w-5 h-5 text-slate-600" />
      )}
    </div>
  );
}
