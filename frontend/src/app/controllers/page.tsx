import { AdjustmentsHorizontalIcon, DevicePhoneMobileIcon } from "@heroicons/react/24/outline";

interface Hotkey {
  action: string;
  binding: string;
}

interface ControllerProfile {
  id: string;
  name: string;
  author: string;
  description: string;
  hotkeys: Hotkey[];
}

const profiles: ControllerProfile[] = [
  {
    id: "retro-game-corps",
    name: "Retro Game Corps",
    author: "Retro Game Corps",
    description:
      "Populair profiel gebaseerd op de configuratie van Retro Game Corps. Optimaal voor handhelds met fysieke knoppen.",
    hotkeys: [
      { action: "Quit", binding: "Select + Start" },
      { action: "Save State", binding: "Select + R1" },
      { action: "Load State", binding: "Select + L1" },
      { action: "Fast Forward", binding: "Select + R2" },
      { action: "Menu", binding: "Select + X" },
      { action: "Screenshot", binding: "Select + B" },
    ],
  },
  {
    id: "techdweeb",
    name: "TechDweeb",
    author: "TechDweeb",
    description:
      "Alternatief profiel gericht op ergonomie tijdens langere sessies. Minder kans op onbedoeld triggeren van hotkeys.",
    hotkeys: [
      { action: "Quit", binding: "L3 + R3" },
      { action: "Save State", binding: "L2 + R1" },
      { action: "Load State", binding: "L1 + R2" },
      { action: "Fast Forward", binding: "L2 + R2" },
      { action: "Menu", binding: "L3 + R2" },
      { action: "Screenshot", binding: "L1 + R1" },
    ],
  },
  {
    id: "emuflow-default",
    name: "EmuFlow Default",
    author: "EmuFlow",
    description:
      "Standaard EmuFlow profiel. Gebalanceerde keuzes die werken op de meeste Android handhelds met een full controller layout.",
    hotkeys: [
      { action: "Quit", binding: "Home (lang indrukken)" },
      { action: "Save State", binding: "Select + R1" },
      { action: "Load State", binding: "Select + L1" },
      { action: "Fast Forward", binding: "Select + A" },
      { action: "Menu", binding: "Select + Y" },
      { action: "Screenshot", binding: "Volume Down + R1" },
    ],
  },
];

export default function ControllersPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Controller Profielen
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Selecteer en beheer hotkey-profielen voor RetroArch en andere emulatoren.
        </p>
      </div>

      {/* Profile Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {profiles.map((profile) => (
          <div
            key={profile.id}
            className="bg-slate-800 rounded-xl border border-slate-700/50 flex flex-col overflow-hidden"
          >
            {/* Card Header */}
            <div className="px-5 py-4 border-b border-slate-700/50 flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-violet-600/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <AdjustmentsHorizontalIcon className="w-5 h-5 text-violet-400" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm font-semibold text-white leading-snug">
                  {profile.name}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  door {profile.author}
                </p>
              </div>
            </div>

            {/* Description */}
            <div className="px-5 py-3 border-b border-slate-700/50">
              <p className="text-xs text-slate-400 leading-relaxed">
                {profile.description}
              </p>
            </div>

            {/* Hotkeys Table */}
            <div className="px-5 py-3 flex-1">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Hotkeys
              </p>
              <table className="w-full text-xs">
                <tbody className="divide-y divide-slate-700/40">
                  {profile.hotkeys.map(({ action, binding }) => (
                    <tr key={action}>
                      <td className="py-1.5 text-slate-400 pr-3">{action}</td>
                      <td className="py-1.5 text-right">
                        <code className="text-violet-300 bg-violet-900/30 px-1.5 py-0.5 rounded text-xs font-mono whitespace-nowrap">
                          {binding}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Apply Button */}
            <div className="px-5 py-4 border-t border-slate-700/50">
              <button
                type="button"
                disabled
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-500 text-sm font-medium rounded-lg cursor-not-allowed"
                title="Koppel eerst een device om dit profiel toe te passen"
              >
                <DevicePhoneMobileIcon className="w-4 h-4" />
                Toepassen op device
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Info banner */}
      <div className="bg-slate-800/60 border border-slate-700/40 rounded-xl px-5 py-4 text-sm text-slate-400">
        <span className="text-slate-300 font-medium">Tip: </span>
        Koppel een device via de{" "}
        <a href="/devices" className="text-violet-400 hover:text-violet-300 underline underline-offset-2">
          Devices pagina
        </a>{" "}
        om een profiel te kunnen toepassen.
      </div>
    </div>
  );
}
