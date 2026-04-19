import {
  DevicePhoneMobileIcon,
  QrCodeIcon,
  WrenchScrewdriverIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";

const tableHeaders = [
  "Device naam",
  "Chipset",
  "Android versie",
  "Status",
  "Laatst gezien",
];

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

export default function DevicesPage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Devices</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Beheer gekoppelde Android-apparaten.
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium rounded-lg transition-colors duration-150"
        >
          <DevicePhoneMobileIcon className="w-4 h-4" />
          Device koppelen
        </button>
      </div>

      {/* Setup Steps */}
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

      {/* Device Table */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">
          Gekoppelde devices
        </h2>
        <div className="bg-slate-800 rounded-xl border border-slate-700/50 overflow-hidden">
          {/* Table header */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  {tableHeaders.map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {/* Empty state row */}
                <tr>
                  <td
                    colSpan={tableHeaders.length}
                    className="px-4 py-16 text-center"
                  >
                    <div className="flex flex-col items-center gap-3">
                      <DevicePhoneMobileIcon className="w-10 h-10 text-slate-600" />
                      <p className="text-slate-400 text-sm font-medium">
                        Nog geen devices gekoppeld
                      </p>
                      <p className="text-slate-600 text-xs">
                        Volg de stappen hierboven om je eerste device te koppelen.
                      </p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
