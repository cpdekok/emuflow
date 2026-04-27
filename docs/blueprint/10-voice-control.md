# 10 — Voice Control en AI Companions

Status: Vision-document — fase 4+ scope, niet in fase 1-3.

## Context

Tijdens fase 1-discussie kwam voice-control op tafel, en daaropvolgend de vraag of AI-gaming-companions (zoals [Questie.ai](https://www.questie.ai)) interessant zijn voor EmuFlow.

Conclusie van die discussie: beide zijn fase 4+ vision, niet kernfeature van EmuFlow. Dit document legt vast wat we wel en niet doen, en waarom.

## Voice control

### Use-cases waar voice waarde toevoegt

1. **Hands-free tijdens gameplay**: "Save state slot 3", "load state", "screenshot", "exit to launcher" — beide handen aan de controller, geen menu nodig
2. **Accessibility**: spelers met beperkte motoriek
3. **Setup/wizard**: "EmuFlow, scan voor controllers"
4. **Game-launch**: "Start Mario Kart" zonder door bibliotheek te scrollen

### Use-cases waar voice NIET werkt

- In-game controls ("jump", "attack") — latency te hoog, herkenning te onbetrouwbaar, sluit slechthorenden uit
- Snelle reacties — gamepad blijft superieur

### Technische opties

| Optie | Latency | Privacy | Kosten | Offline |
|---|---|---|---|---|
| Android `SpeechRecognizer` (on-device) | ~300ms | Lokaal | Gratis | Ja (Android 13+) |
| `whisper.cpp` (lokaal model) | ~500ms | Lokaal | Gratis | Ja |
| Picovoice Porcupine (wake-word) | ~150ms | Lokaal | Gratis tier 3 wake-words | Ja |
| Cloud STT (Google/OpenAI) | ~800ms | Cloud | Per-minuut | Nee |

### EmuFlow-keuze

**Picovoice Porcupine wake-word ("Hey EmuFlow") + Android on-device SpeechRecognizer voor commands.**

Volledig lokaal, geen cloud-afhankelijkheid, geen audio-uploads. Past bij onze privacy-positie.

### Scope per fase

- **Fase 4 P0**: wake-word + 10 basis-commando's (save/load state 1-5, screenshot, exit, pause, resume)
- **Fase 4 P1**: game-launch via naam, configuratie-commands ("schakel Vulkan in")
- **Fase 5 P2**: multi-language (NL/EN/DE/FR), custom commando's per gebruiker

### Won't have

- In-game voice-controls (zoals "jump", "attack")
- Cloud-STT zonder lokale fallback
- Always-listening zonder wake-word

### Hardware-vereisten

- Mic dichtbij speler (handheld speakers werken meestal, tablet ook, phone het beste)
- Stille omgeving of noise-cancelling
- Push-to-talk op controller-back-button als alternatief voor wake-word

RP5, Odin 2, RG556 hebben allemaal ingebouwde mics — fase 1-3 hardware is dus al voice-capable, maar het is niet onze prioriteit.

## AI Companions (Questie en soortgelijk)

### Marktreferentie

[Questie.ai](https://www.questie.ai) — AI-companion die scherm leest via Vision Language Model en realtime voice-chat geeft. 25.000+ gebruikers, $19.99 per 25 uur. Gericht op moderne PC-games, Twitch-streamers, roleplay.

Andere referenties: Razer Ava, Soulmate (Meta Quest), Quest Portal (TTRPG).

### Waarom geen kernfeature voor EmuFlow

**1. Doelgroep-mismatch**

EmuFlow's doelgroep: retrogamers 30-55, nostalgie-gedreven, spelen klassiekers die ze al uit hun hoofd kennen, solo op de bank. Een babbelende AI die zegt "hé, je had die ster moeten pakken" tegen iemand die Mario Kart Wii al sinds 2008 speelt = irritant, niet immersief.

Questie's doelgroep: PC-gamers die moderne titels spelen, Twitch-streamers die "dead air" willen vullen, roleplay-zoekers.

**2. Technische obstakels op handhelds**

- Battery drain: VLM + mic + cloud-LLM = 30-40% extra accugebruik
- Performance hit: PS2-emulatie zit al op 90% GPU; screen-capture erbij = framedrops
- Cloud-afhankelijkheid: wifi vereist, latency, abonnementskosten

**3. Privacy-conflict met onze positie**

Wij positioneren EmuFlow als "we collecteren geen content" (DSA art. 6). Questie integreren betekent: screen-frames + audio + game-context naar Questie's cloud. Ondermijnt onze juridische positie.

### Drie scenario's voor toekomstige integratie

#### Scenario A — Optionele deeplink-integratie (fase 4+)

EmuFlow toont in de game-launcher een knop "AI Companion" die Questie's app opent met game-ID context (geen ROM, geen save-state). Geen diepe integratie, gebruiker kiest zelf.

- Voordeel: gebruikers die het willen, kunnen het, wij dragen geen verantwoordelijkheid
- Nadeel: geen toegevoegde waarde voor EmuFlow zelf

#### Scenario B — Eigen lichtgewicht "retro-coach" (fase 5+)

On-device kleine LLM (Gemma 2B / Phi-3 Mini via MLC-LLM op Adreno) die alleen tekst-tips geeft uit een vooraf-gecureerde walkthrough-database voor klassiekers. Geen vision, geen voice, geen cloud.

Voorbeeld: "Tip voor Final Fantasy VII: na disc 1 kun je niet meer terug naar het Forgotten Capital."

- Voordeel: blijft binnen privacy-belofte, geen abonnement, on-device
- Nadeel: bouw-werk, niet "magisch"

#### Scenario C — Negeren voor nu

Geen integratie, wel monitoren of testers ernaar vragen.

### Beslissing

**Scenario C voor fase 1-3.** Reden:

1. Retrogamer-testers zullen hier niet om vragen
2. Eerst kernpijnpunten: clean-slate, BIOS-flow, crashdetectie, knoppen-mapping
3. Als testers in fase 3 spontaan vragen om AI-coach → herzien

Indien herziening: **Scenario B (eigen retro-coach) heeft voorkeur boven A (Questie-integratie)** vanwege privacy-positie en geen externe afhankelijkheid.

## Won't have (expliciet)

- Cloud-AI-companion-integratie zonder lokale fallback
- Always-on screen-spectating (privacy + performance)
- Voice-driven in-game controls
- Roleplay-companions of "AI girlfriend"-functionaliteit (niet onze markt)

## Open vragen

- Werkt MLC-LLM betrouwbaar op Adreno-GPU's van handhelds (ipv. flagship phones)?
- Bestaat er een opensource walkthrough-database (GameFAQs is niet bruikbaar wegens TOS)?
- Hoeveel testers vragen spontaan om AI-features in fase 3?
