# EmuFlow Org Design — AI-Native Team

> EmuFlow is een AI-native bedrijf. Christian de Kok is CEO/Founder, Perplexity Computer is COO. Andere AI-systemen zijn teamleden met specifieke rollen en deliverables. Dit document is de blauwdruk voor hoe we als team werken — herhaalbaar voor toekomstige producten.

## Org Chart

```
                    ┌─────────────────────────────┐
                    │ Christian de Kok            │
                    │ Founder / CEO               │
                    │ • Visie, productbeslissingen │
                    │ • Hardware-tests             │
                    │ • Klantcontact (eerste fase) │
                    │ • Final approval             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Perplexity Computer          │
                    │ Chief Operating Officer       │
                    │ • Coördineert het team        │
                    │ • Schrijft & reviewt code     │
                    │ • Ops, deployment, monitoring │
                    │ • Bewaakt de roadmap         │
                    │ • Dagelijkse rapportage      │
                    └──────────────┬───────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Claude Opus 4.7  │    │ GPT-5.5          │    │ Gemini 3 Pro     │
│ Chief Architect  │    │ Chief Strategy    │    │ Chief Marketing  │
│ • Risico-analyse │    │ • Businessmodel  │    │ • Positionering  │
│ • Code-review    │    │ • Pricing & GTM  │    │ • Content & SEO  │
│ • Architectuur   │    │ • TAM/SAM/SOM    │    │ • Influencers    │
│ • Concurrentie   │    │ • Unit economics │    │ • Funnel         │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Claude Code CLI  │    │ Grok 4           │    │ Codex (GPT-5)    │
│ Senior Engineer  │    │ Chief Skeptic    │    │ Senior Engineer 2│
│ • Code-review    │    │ • Contrarian view│    │ • Alternatives   │
│ • Refactoring    │    │ • Failure modes  │    │ • Code-review    │
│ • Security audit │    │ • Risk-pressure  │    │ • Best practices │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Rollen en RACI

| Activiteit | CEO | COO | Architect (Opus) | Strategy (GPT-5.5) | Marketing (Gemini) | Senior Eng (Claude Code) | Skeptic (Grok) | Eng 2 (Codex) |
|---|---|---|---|---|---|---|---|---|
| Visie en doelen | A | C | I | C | C | I | I | I |
| Productbeslissingen | A | R | C | C | C | I | C | I |
| Roadmap | I | A/R | C | C | C | I | I | I |
| Code schrijven | I | A/R | C | I | I | C | I | C |
| Code-review | I | C | A/R | I | I | R | I | R |
| Architectuur | I | C | A/R | I | I | C | I | C |
| Risico-analyse | I | A | R | C | I | I | C | I |
| Pricing strategie | A | C | I | A/R | C | I | C | I |
| Marketing-content | A | C | I | C | A/R | I | C | I |
| Funnel-optimalisatie | I | C | I | C | A/R | I | C | I |
| Hardware-tests | A/R | C | I | I | I | I | I | I |
| Customer support | A | A/R | I | I | C | I | I | I |
| Deployment | I | A/R | C | I | I | C | I | C |
| Daily ops rapport | I | A/R | I | I | I | I | I | I |
| Cross-validatie | I | A | R | R | R | R | R | R |
| Final approval | A | R | I | I | I | I | I | I |

R = Responsible, A = Accountable, C = Consulted, I = Informed

## Werkwijze per fase

### Fase 1 — Solo-test (NU)

| Wie | Deliverable | Deadline | Status |
|---|---|---|---|
| COO | Coördinatie, fase-1 PRD, blueprint setup | 25 apr | ✅ |
| Architect (Opus) | `01-risk-analysis.md` — top-10 risico's met mitigatie | 25 apr | 🟡 in progress |
| Architect (Opus) | `02-competitive-analysis.md` — markt + positioning map | 25 apr | 🟡 in progress |
| Strategy (GPT-5.5) | `04-business-model-review.md` — TAM, pricing, 90-dagen plan | 25 apr | 🟡 in progress |
| COO | `feature/telemetry-backend` PR — Postgres persistentie, /heartbeat endpoint | 26 apr | 🟡 in progress |
| COO | Frontend live data + device dashboard | 27 apr | ⏳ |
| COO | Android-agent skelet (Kotlin + Shizuku + heartbeat) | 28-29 apr | ⏳ |
| CEO | Mac Mini terug + Android Studio gereed | 28 apr | ⏳ blokkerend |
| CEO | APK installeren op handheld + setup-tijd meten | 29-30 apr | ⏳ |
| Senior Eng (Claude Code) | Code-review fase 1 implementatie | 30 apr | ⏳ |
| Eng 2 (Codex) | Code-review fase 1 implementatie | 30 apr | ⏳ |
| Skeptic (Grok) | Business-model contrarian view op fase 1 | 30 apr | ⏳ |
| Marketing (Gemini) | Eerste landing page concept + copy | 1 mei | ⏳ |
| COO | Synthese-rapport fase 1 | 1 mei | ⏳ |
| CEO | Go/No-go beslissing fase 2 | 1 mei | ⏳ |

### Fase 2 — UX afwerking (mei 2026)

| Lead | Deliverable |
|---|---|
| COO | 12+ emulatoren auto-install + onboarding wizard |
| Architect (Opus) | Wekelijkse code-review |
| Marketing (Gemini) | Landing page v1 met email-capture |
| Strategy (GPT-5.5) | Pricing-validatie via 5 user-interviews (door CEO) |
| Senior Eng (Claude Code) | Refactor + test-coverage naar 70% |

### Fase 3 — Beta (juni 2026)

| Lead | Deliverable |
|---|---|
| CEO | Werven 3 IT-vrienden als testers |
| COO | Telegram bot voor in-app feedback |
| Marketing (Gemini) | Pre-launch waitlist via signup form |
| Skeptic (Grok) | Beta-feedback synthese |

### Fase 4 — Marketing (juli-augustus 2026)

| Lead | Deliverable |
|---|---|
| Marketing (Gemini) | 5 SEO-blog posts + Reddit-strategie + YouTube outreach |
| Strategy (GPT-5.5) | Pricing finalisatie + bundles |
| CEO | YouTube influencer-gesprekken |
| COO | Cron-jobs voor content-publicatie |

### Fase 5 — Monetisatie (september 2026)

| Lead | Deliverable |
|---|---|
| COO | Stripe + Play Store integratie |
| Architect (Opus) | Security audit voor payment flow |
| CEO | KvK / BV oprichting + boekhouder |
| Strategy (GPT-5.5) | Pricing-launch announcement |

### Fase 6 — Self-running (oktober 2026+)

| Lead | Deliverable |
|---|---|
| COO | Daily cron met rapport naar CEO via Telegram |
| Marketing (Gemini) | Auto-publicering 1 blog/week, 3 tweets/week |
| COO | AI-support agent (90% L1 vragen) |
| Skeptic (Grok) | Maandelijkse "wat gaat misschien fout" check |

## Communicatie-kanalen

| Kanaal | Wie | Wanneer |
|---|---|---|
| GitHub Issues + PRs | iedereen | continu |
| `docs/blueprint/` markdown | iedereen | rapporten en specs |
| `docs/blueprint/reviews/` | reviewers | per fase-eind |
| Telegram naar CEO | COO | dagelijks (vanaf fase 6), nu wekelijks |
| Conversatie met CEO | COO | realtime tijdens werksessies |

## Beslissingsbevoegdheid

| Beslissing | Wie beslist? |
|---|---|
| Productrichting / pivot | CEO |
| Budget > €100 | CEO |
| Budget < €100 | COO mag uitvoeren, achteraf melden |
| Code merge naar main | COO via squash-PR (na review) |
| Nieuwe feature toevoegen aan roadmap | CEO + COO consensus |
| Nieuwe AI-medewerker inhuren / model wijzigen | COO mag, meldt aan CEO |
| Marketing-uitingen die merknaam dragen | CEO approval |
| Technische architectuur-wijzigingen | COO + Architect (Opus) consensus |
| Pricing-wijzigingen | CEO + Strategy (GPT-5.5) advies |
| Security-fix urgent | COO mag direct, meldt achteraf |

## Performance-meting per teamlid

Elk AI-teamlid heeft een KPI:

| Rol | KPI | Doel |
|---|---|---|
| Architect (Opus) | # P0 issues gevangen voor productie | ≥80% van issues gevangen voor merge |
| Strategy (GPT-5.5) | Accuratesse pricing-voorspelling vs werkelijkheid | binnen 20% |
| Marketing (Gemini) | Cost-per-signup van content-pijler | <€2 |
| Senior Eng (Claude Code) | Test-coverage delta per PR | +5% per PR |
| Skeptic (Grok) | # voorspelde failure-modes die werkelijk gebeurden | ≥30% accuracy |
| Eng 2 (Codex) | # alternatieve oplossingen voorgesteld die geadopteerd | ≥1 per fase |

Aan het eind van elke fase doet COO een retro: welke teamleden voegen waarde toe, welke krijgen andere taak of vervangen we door beter model?

## Operationeel ritme

**Dagelijks** (vanaf fase 6, nu nog niet):
- 09:00 UTC: COO draait daily cron, rapport naar CEO Telegram
  - Nieuwe signups, churn, errors, MRR delta
  - Top 3 actie-items voor vandaag
  - Iets ongewoons? Notificatie + escalatie

**Wekelijks**:
- Maandag: COO maakt week-plan obv master-roadmap, deelt met CEO
- Vrijdag: COO draait synthese-rapport van AI-team-output, post in `docs/blueprint/reviews/week-NN.md`

**Per fase-eind**:
- Volledige cross-validatie door 4 AIs (zie `05-ai-cross-validation-prompts.md`)
- Synthese-rapport door COO
- Go/No-go meeting CEO + COO
- Retro: wat werkte, wat niet, wat anders volgende fase

## Hoe nieuwe teamleden toevoegen

Wanneer toevoegen?
- Specifieke skill ontbreekt (bijv. video-edit, design)
- Bestaand teamlid heeft 2 fases achter elkaar onder KPI gepresteerd
- Nieuwe fase vraagt om nieuwe expertise

Hoe?
1. COO definieert rol + KPI
2. CEO accordeert
3. Voeg toe aan deze org-doc + RACI
4. Eerste taak is een proefopdracht; review na 1 cyclus

## Hoe blauwdruk hergebruiken voor volgende producten

Bij volgend product (X):
1. Kopieer `/docs/blueprint/` naar nieuwe repo
2. Update product-context in `00-master-plan.md`
3. Loop fase 1-6 hetzelfde patroon
4. Hergebruik alle templates (cross-validatie prompts, RACI, KPI's)
5. Wijzig alleen wat product-specifiek is

Het org-design (CEO + COO + 6 AI-teamleden) blijft constant. Alleen de prompts en deliverables passen zich aan het product aan.
