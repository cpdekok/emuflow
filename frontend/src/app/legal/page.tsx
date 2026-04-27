import {
  ShieldExclamationIcon,
  ScaleIcon,
  DocumentTextIcon,
  CubeTransparentIcon,
  HandRaisedIcon,
} from "@heroicons/react/24/outline";

export const metadata = {
  title: "Juridisch | EmuFlow",
  description:
    "Disclaimer, gebruiksvoorwaarden en juridische uitgangspunten van EmuFlow.",
};

export default function LegalPage() {
  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Juridisch
        </h1>
        <p className="text-slate-400 mt-1 text-sm">
          Disclaimer, gebruiksvoorwaarden en juridische uitgangspunten.
        </p>
      </div>

      {/* TL;DR banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 flex items-start gap-3">
        <ShieldExclamationIcon className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-2">
          <p className="text-sm font-semibold text-amber-200">
            Korte samenvatting
          </p>
          <ul className="text-sm text-amber-100/90 space-y-1.5 list-disc pl-4">
            <li>
              EmuFlow installeert, configureert en updatet open-source emulators
              die jij zelf op je eigen Android-apparaat gebruikt.
            </li>
            <li>
              EmuFlow levert <strong>geen</strong> ROM&apos;s, BIOS-bestanden,
              save-states of andere auteursrechtelijk beschermde content. Die
              voeg jij zelf toe en moet je rechtmatig in bezit hebben.
            </li>
            <li>
              ROM- en save-bestanden blijven <strong>uitsluitend lokaal</strong>{" "}
              op je apparaat. Ze worden nooit naar onze servers gestuurd.
            </li>
            <li>
              Je gebruikt EmuFlow op eigen risico. Wij zijn niet aansprakelijk
              voor dataverlies, onbeschikbaarheid van vendor-software of
              schade aan je apparaat.
            </li>
          </ul>
        </div>
      </div>

      {/* Sections */}
      <Section
        icon={DocumentTextIcon}
        title="1. Wat EmuFlow doet — en wat niet"
      >
        <p>
          EmuFlow is een Android-app en bijbehorende webconsole die het
          installatie-, update- en configuratieproces van bestaande emulators
          (zoals Citra, Dolphin, AetherSX2, RetroArch, ePSXe en vergelijkbare)
          automatiseert. EmuFlow zelf bevat geen emulatorcode — die wordt
          opgehaald van de officiële distributiekanalen van de respectieve
          projecten.
        </p>
        <p className="mt-3">
          EmuFlow biedt geen ROM&apos;s, BIOS-images, originele
          spelassets, save-states van derden of vergelijkbare beschermde
          inhoud aan, en geeft daar geen toegang toe via deze app.
        </p>
      </Section>

      <Section icon={CubeTransparentIcon} title="2. ROM- en BIOS-eigendom">
        <p>
          Voor het draaien van originele software heb je een eigen, rechtmatig
          verkregen kopie nodig van het spel en (waar van toepassing) de
          bijbehorende BIOS. Of een dergelijke dump in jouw rechtsgebied is
          toegestaan, hangt af van lokale wetgeving (zie bijv. de Auteurswet,
          art. 16b voor privé-kopieën in Nederland, en EU-Richtlijn 2001/29).
          EmuFlow beoordeelt dit niet voor je en draagt geen verantwoordelijkheid
          voor jouw bronbestanden.
        </p>
        <p className="mt-3">
          BIOS-bestanden worden uitsluitend lokaal gevalideerd via SHA-256
          hash-vergelijking met een referentiedatabase. De BIOS zelf verlaat je
          apparaat nooit. Hashes en metadata van jouw BIOS worden niet naar
          onze servers verzonden.
        </p>
      </Section>

      <Section icon={ScaleIcon} title="3. Save-bestanden en ROM-koppeling">
        <p>
          De Save Vault houdt back-ups bij van save-bestanden en save-states op
          je apparaat. Saves blijven{" "}
          <strong>volledig lokaal opgeslagen</strong>; cross-device synchronisatie
          wordt in een latere fase toegevoegd en zal dan zero-knowledge
          end-to-end versleuteld werken (de server kan inhoud niet inzien).
        </p>
        <p className="mt-3">
          ROM-bestandshashes worden uitsluitend lokaal gebruikt om saves aan
          het juiste spel te koppelen. ROM-hashes en bestandsnamen worden{" "}
          <strong>niet</strong> naar onze servers verzonden, in lijn met
          Digital Services Act art. 6 en algemene zorgplicht ten aanzien van
          mogelijk onrechtmatige content.
        </p>
      </Section>

      <Section icon={DocumentTextIcon} title="4. Telemetrie en privacy">
        <p>
          De EmuFlow Agent stuurt op gezette tijden telemetrie naar onze
          servers om de werking te verbeteren. Het gaat om:
        </p>
        <ul className="list-disc pl-5 mt-2 space-y-1">
          <li>Hardware-fingerprint (gehashte combinatie van device-eigenschappen)</li>
          <li>Apparaatnaam, chipset, GPU-familie, RAM, Android-versie en page size</li>
          <li>Geïnstalleerde emulatorpakketten en -versies</li>
          <li>Anonieme crash-events: stacktrace-hash, signaal, geheugenstatus, thermal state</li>
          <li>
            Geaggregeerde save-statistieken (aantallen saves, vault-grootte,
            backup-fouten — geen ROM-namen of inhoud)
          </li>
          <li>Batterijniveau, batterij- en CPU/GPU-temperatuur</li>
        </ul>
        <p className="mt-3">
          Persoonsgegevens, accountnamen, e-mailadressen, contactlijsten,
          locatiegegevens, ROM-bestandsnamen, save-inhoud en BIOS-bestanden
          worden <strong>niet</strong> verzonden. Telemetrie is in fase 1
          standaard aan; je kunt dit op elk moment uitschakelen in de Agent-app.
        </p>
      </Section>

      <Section icon={HandRaisedIcon} title="5. Vendor-shells en clean-slate">
        <p>
          Sommige Android-handhelds (waaronder die van AYANEO en Retroid)
          komen met fabrikant-specifieke launchers en hulppakketten. EmuFlow
          biedt een &quot;clean-slate&quot;-flow waarmee je deze pakketten
          optioneel kunt verwijderen of uitschakelen. Standaardinstelling
          (&quot;Default A&quot;) is om vendor-shells uitgeschakeld te laten.
        </p>
        <p className="mt-3">
          Het uitschakelen van vendor-software kan invloed hebben op
          garantievoorwaarden, OTA-updates of andere functies van je apparaat.
          Je voert deze handelingen op eigen risico uit. EmuFlow is niet
          verbonden aan en wordt niet onderschreven door enige
          hardware-fabrikant.
        </p>
      </Section>

      <Section icon={ScaleIcon} title="6. Aansprakelijkheid">
        <p>
          EmuFlow wordt &quot;as-is&quot; geleverd, zonder enige expliciete of
          impliciete garantie van werking, verhandelbaarheid of geschiktheid
          voor een bepaald doel. Voor zover wettelijk toegestaan zijn wij niet
          aansprakelijk voor directe of indirecte schade voortvloeiend uit het
          gebruik van EmuFlow, waaronder dataverlies, hardware-schade,
          onbeschikbaarheid van diensten of het verlies van vendor-functies.
        </p>
      </Section>

      <Section icon={DocumentTextIcon} title="7. Handelsmerken">
        <p>
          Alle genoemde productnamen, merken en handelsmerken zijn eigendom van
          hun respectieve eigenaren. Verwijzing naar specifieke apparaten
          (Retroid, AYANEO en andere) of emulators (Citra, Dolphin, AetherSX2,
          RetroArch en andere) impliceert geen samenwerking of goedkeuring door
          die partijen.
        </p>
      </Section>

      <Section icon={DocumentTextIcon} title="8. Contact en wijzigingen">
        <p>
          Vragen of meldingen over deze pagina kun je richten aan{" "}
          <a
            href="mailto:legal@emuflow.app"
            className="text-violet-300 hover:text-violet-200 underline"
          >
            legal@emuflow.app
          </a>
          . Wij behouden ons het recht voor deze tekst aan te passen; de
          actuele versie is altijd op deze pagina te raadplegen.
        </p>
      </Section>

      <p className="text-xs text-slate-500 pt-4 border-t border-slate-800">
        Laatst bijgewerkt: 27 april 2026 — versie 0.1 (fase 1 solo-test).
        Deze tekst is een voorlopige juridische uitgangspositie en geen
        formele algemene voorwaarden. Definitieve voorwaarden volgen vóór
        publieke release.
      </p>
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700/50 p-5">
      <div className="flex items-center gap-3 mb-3">
        <Icon className="w-5 h-5 text-violet-400" />
        <h2 className="text-lg font-semibold text-white">{title}</h2>
      </div>
      <div className="text-sm text-slate-300 leading-relaxed">{children}</div>
    </section>
  );
}
