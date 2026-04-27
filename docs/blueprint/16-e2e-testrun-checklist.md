# 16 — End-to-end testrun checklist

> Doc-status: handmatige checklist voor de eerste solo-test op fysieke hardware.
> Tester: Christian (notary-retrogamer founder).
> Devices: Retroid Pocket Mini (eerst), AYANEO Pocket Micro Classic (tweede).
> Voorwaarde: USB-C → USB-A 2.0 OTB-kabel binnen.

## Pre-test setup (≤ 30 min)

- [ ] **Beide handhelds** opgeladen tot ≥ 80%
- [ ] Werk-PC: ADB tools geïnstalleerd (`platform-tools` van Android), test via `adb devices`
- [ ] EmuFlow Agent APK gedownload van GitHub Releases (laatste main-build)
- [ ] Backend live: `curl https://backend-production-05dd.up.railway.app/health` ⇒ `{"status":"ok"}`
- [ ] Frontend live: [emuflow.app/devices](https://emuflow.app/devices) toont verwachte handhelds (al geseed)
- [ ] Telemetrie-dashboard open in tabblad: [emuflow.app/admin/telemetry](https://emuflow.app/admin/telemetry)

## Run 1 — Retroid Pocket Mini

### A. Install Agent

- [ ] Shizuku installeren via Google Play
- [ ] Shizuku activeren via Wireless Debugging (Android 11+)
- [ ] EmuFlow Agent APK installeren (sideload via OTB-kabel)
- [ ] Agent openen, accepteer Shizuku-koppeling
- [ ] Eerste heartbeat verschijnt op /devices binnen 60s

### B. Pre-flight wizard

- [ ] /setup → kies Retroid Pocket Mini
- [ ] Verwacht: alle 9 checks groen (Shizuku, page size 4 KB, batterij ≥ 50%, controllers dual_stick, geen vendor-shells van betekenis)
- [ ] Indien rood: noteren, screenshot, ticket aanmaken in [GitHub issues](https://github.com/cpdekok/emuflow/issues)

### C. Clean-slate

- [ ] Default A bevestigen (vendor-shells laten staan)
- [ ] Plan-pagina: review uitvoer
- [ ] Plan bevestigen (uitvoering komt fase 2)

### D. Eerste emulator install (handmatig fase 1)

- [ ] PPSSPP installeren via Agent (auto-match: 4 KB build, arm64-v8a, stable, Vulkan)
- [ ] Eigen ROM laden (origineel, eigen bezit) — bijv. een PSP-game waarvan jij de UMD bezit
- [ ] 30 min spelen, ten minste 3 saves maken (in-game + savestate)

### E. Save Vault validatie

- [ ] Op /sdcard/EmuFlow_Vault/org.ppsspp.ppsspp/ verschijnen vault-kopieën
- [ ] SHA-256 van kopie matcht originele save (handmatig: `sha256sum` op beide)
- [ ] Maximaal 10 versies per slot (rolling buffer)
- [ ] Geen ROM-naam, hash of inhoud in de heartbeat-payload (verifieer in /admin/telemetry → save_events_24h)

### F. Crash detectie (optioneel)

- [ ] Forceer een crash: PPSSPP met onmogelijke graphics setting
- [ ] Crash-event verschijnt op /devices/<id>/events
- [ ] Stacktrace-hash zichtbaar; tombstone-excerpt < 4096 chars

### G. Telemetrie steekproef

- [ ] /admin/telemetry: thermal state niet boven MODERATE
- [ ] Heartbeat lag < 60s
- [ ] Backup-fouten = 0

## Run 2 — AYANEO Pocket Micro Classic

Herhaal A–G, met aandacht voor AYANEO-specifieke quirks (doc 14):

- [ ] **B. Pre-flight**: verwacht `controllers: no_stick` waarschuwing — D-pad+face-buttons profiel
- [ ] **B. Pre-flight**: vendor-shells warn met 4 pakketten (`com.ayaneo.*`)
- [ ] **C. Clean-slate**: probeer eenmalig optie B → schakel alleen `com.ayaneo.gamemanager` uit (minst risicovolle)
- [ ] **C**: Direct daarna re-enable via Shizuku command (handmatig) om dichotomie te testen
- [ ] **D. Install**: PPSSPP **OpenGL-ES-build** (niet Vulkan — Mali-G57 doc 14)
- [ ] **D**: USB-C audio → BT pairen alvorens te spelen (geen 3.5mm jack)
- [ ] **E. Save Vault**: extra goed letten op file-locking issues (USB-shared-data quirk)
- [ ] **F. Crash**: bij ePSXe of Citra, niet bij PPSSPP

## Post-test debrief

- [ ] Alle screenshots in dropbox `/EmuFlow/test-runs/2026-04-XX/`
- [ ] Issues gelogd: titel, severity (P0/P1/P2), device, reproductiestappen
- [ ] /admin/telemetry export: download CSV van device-list voor analyse
- [ ] Update [docs/blueprint/00-master-plan.md](./00-master-plan.md) met "fase 1 solo-test afgerond" + datum
- [ ] Beslis fase 2 scope: gaan we breder testen of eerst issues fixen

## Pas verder als...

- [ ] **0 P0-issues open** (P0 = installatie crasht, save-data verlies, niet-werkende controllers, vendor-shell killed unintentionally)
- [ ] **Crash-rate ≤ 1 per 30 min spelen** voor de geteste emulators
- [ ] **Heartbeat success-rate ≥ 99%** over de testperiode
- [ ] **Save Vault corruptie-rate = 0**

Pas dan beginnen we met externe testers (fase 2 — small alpha, max 10 testers via gerichte uitnodiging).
