# AI Cross-Validatie Templates — Blauwdruk

Voor elke fase van EmuFlow (en toekomstige producten) worden 4 AI-systemen ingezet voor onafhankelijke review. Dit document bevat de standaard-prompts.

## Werkwijze

1. Voor elke milestone (eind van een fase) wordt code + docs op `main` branch gezet
2. Christian (of de agent) draait deze prompts via:
   - **Claude Code** (CLI tool via Anthropic) — code review
   - **OpenAI Codex / GPT-5** — code + alternatives
   - **Grok 4** — contrarian view, business
   - **Gemini 3 Pro** — productstrategie, marketing
3. Outputs worden opgeslagen in `docs/blueprint/reviews/<fase>-<ai>.md`
4. Een 5e AI (rotatie) maakt synthese-rapport in `docs/blueprint/reviews/<fase>-summary.md`
5. Synthese identificeert: P0/P1/P2 issues, conflicting opinions (waar 4 AIs disagreen), unanimous recommendations

## Prompt 1 — Code Review (Claude Code, OpenAI Codex)

```
Je krijgt toegang tot github.com/cpdekok/emuflow (public repo).

Review specifiek de fase-N implementatie. Loop het volgende langs:

1. **Security**
   - Authentication & authorization (zijn er endpoints zonder auth die het wel zouden moeten hebben?)
   - SQL injection, XSS, CSRF
   - Secret management (geen hardcoded keys)
   - Dependency vulnerabilities (check package versies)
   - Rate limiting waar nodig

2. **Architectuur**
   - Separation of concerns (frontend / backend / android-agent)
   - Database schema-correctheid en index-strategie
   - API contract-stability (versioning, deprecation pad)
   - Async patterns goed toegepast?

3. **Tests**
   - Test-coverage > 70% backend, > 50% frontend?
   - Edge cases gedekt?
   - Mock vs integration balance

4. **Performance**
   - N+1 queries
   - Caching strategie (Redis ingezet waar nuttig?)
   - Frontend bundle size, code splitting

5. **Maintainability**
   - Type hints, docstrings, JSDoc waar nodig
   - Naming consistentie (NL vs EN)
   - Dead code, TODO's, FIXME's

Lever rapport in markdown met:
- Top 5 P0 issues (must-fix voor release)
- Top 5 P1 issues (fast-follow)
- Top 5 P2 nice-to-haves
- Aparte sectie "Architectural concerns" met diagrammen indien nuttig
- Aparte sectie "Praise" — wat is goed gedaan

Wees concreet: bestand:regelnummer + voorgestelde fix.
```

## Prompt 2 — Business Model Critique (Grok)

```
Je bent een scherpe contrarian VC met 15 jaar consumer SaaS ervaring. Je krijgt EmuFlow's huidige status (URL, blueprint docs, pricing-plan, marktpositie).

Tear it apart. Specifiek:

1. **Marktomvang** — is de TAM/SAM/SOM realistisch of overschat?
2. **Pricing** — €49 lifetime / €5/mnd / freemium — welke faalt het hardst en waarom?
3. **Defensibility** — wat houdt Retroid of Anbernic tegen om dit gratis te bouwen?
4. **CAC / LTV** — werkt de unit-economics voor een solo-founder?
5. **Survival metric** — wat is de ene meetwaarde die over 12 maanden bepaalt of EmuFlow leeft of dood is?
6. **Killer scenarios** — schets 3 manieren waarop EmuFlow in 6 maanden failliet gaat
7. **Pivot-suggesties** — als dit faalt, wat zou je dezelfde codebase op richten?

Wees brutaal eerlijk. Christian heeft geen behoefte aan complimenten — hij wil weten waar het misgaat.
```

## Prompt 3 — Product Strategy + Marketing (Gemini)

```
Je bent een product- en marketing-strategist die 10+ niche consumer apps heeft gelanceerd. Review EmuFlow.

Context: Android handheld auto-setup tool, doelgroep retro-gaming enthousiasten, productie-URL emuflow.app.

Geef strategisch advies op:

1. **Productpositionering**
   - Past de huidige messaging bij wat de markt eigenlijk koopt?
   - Welke alternatieve framings zijn sterker?
   - Welke 3 features zijn echte differentiators vs noise?

2. **Go-to-Market sequencing**
   - Welke launch-volgorde geeft hoogste momentum: blog → Reddit → YouTube influencer → Product Hunt?
   - Welke launch-fout maken solo-developers in deze niche?

3. **Content-strategie**
   - Welke 5 SEO-onderwerpen scoren best voor "best emulator setup [device]"?
   - Welke YouTube-influencers zijn match voor sponsored content (kosten/bereik/conversie)?
   - Welke Reddit-AMA's of community moments vergroten reach?

4. **Onboarding-funnel**
   - Aan de hand van EmuFlow website + app: waar lekt de funnel?
   - Welke 3 gedragsmetrics moeten gemeten worden?
   - Wat is de "aha moment" voor een nieuwe gebruiker?

5. **Pricing & Packaging**
   - Welke prijs-anker werkt psychologisch best?
   - Free trial vs gratis tier?
   - Bundles met handheld-resellers?

Output: concreet, getallen waar mogelijk, en wees bereid mee te denken met de tegenhanger Grok-analyse als die ook is gedeeld.
```

## Prompt 4 — Marketingstrategie validatie (Claude / Gemini)

```
Review het 90-dagen marketingplan in /docs/blueprint/04-business-model-review.md

Voor elke week 1-12:
1. Is het doel meetbaar?
2. Zijn de tactieken realistisch voor een solo-founder met deeltijd inzet?
3. Welke week heeft hoogste risico op slippage?
4. Welke afhankelijkheid moet vooruitgeschoven worden?
5. Wat is de minimum-input om elke milestone te halen?

Lever per week: Status (groen/oranje/rood), risico, suggestie.
```

## Synthese-template

```
Je krijgt 4 review-rapporten over fase-N van EmuFlow. Maak een synthese.

Output structuur:
1. **Unanimous P0 issues** — issues waar ≥3 AIs het over eens zijn
2. **Conflicting opinions** — waar AIs disagreen, met argumenten van beide kanten
3. **P1 fast-follows** — minor issues die Christian volgende sprint moet meenemen
4. **Strategic insights** — niet-technische aanbevelingen waar consensus over is
5. **Action items** — concreet, met owner (Christian / agent) en deadline
6. **Updated risk register** — nieuwe risico's geïdentificeerd
7. **Pivot-signals** — moeten we bijsturen op basis van deze reviews?

Houd het kort: max 1500 woorden. Christian leest dit op zijn telefoon.
```

## Cadans

| Fase | Wie reviewt | Wanneer |
|---|---|---|
| Fase 1 (solo-test) | Alle 4 + synthese | Voor fase-1 acceptance |
| Fase 2 (UX) | Code reviewers (Claude Code, Codex) | Wekelijks tijdens fase 2 |
| Fase 3 (beta) | Business (Grok) + UX (Gemini) | Voor beta-launch |
| Fase 4 (marketing) | Marketing (Gemini) + contrarian (Grok) | Voor public launch |
| Fase 5 (monetisatie) | Alle 4 + legal-focus | Voor eerste betaling |
| Fase 6 (autonoom) | Alle 4 op het AI-agent design | Voor productie-cron-deployment |
