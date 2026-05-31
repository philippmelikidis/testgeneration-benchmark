# Web-UI Testfallgenerierung — LLM vs. traditionell

Empirische Werkbank zum Methodenentwurf (Fricke / Melikidis, HS Reutlingen).
Drei Generierungs-Pipelines auf denselben Ziel-Anwendungen, bewertet durch eine
gemeinsame Metrik-Suite und auf ISO/IEC 25010 *Functional Suitability* abgebildet.
User-Stories steuern Methode 2 und dienen als gemeinsamer Bewertungsmaßstab
(siehe unten).

| Pipeline | Artefakt | Methode | Kurz |
|----------|----------|---------|------|
| Crawler   | `Skript_C` | 1 (traditionell) | autonomer Playwright-Crawler, Zustandsgraph → pytest-Skript; **ohne** User-Story |
| LLM-Agent | `Skript_L` | 1 (LLM-only)     | gleiche Aufgabe wie der Crawler (App autonom erkunden, Testsuite erzeugen); **ohne** User-Story |
| Hybrid    | `Skript_H` | 2 (Aufsatz)      | LLM verfeinert `Skript_C` **mit** User-Story (+ optionalem Fachkontext): Locator, Assertions, Lesbarkeit |

**Methode 1 — fairer A/B ohne Anforderungen:** Crawler und LLM-Agent bekommen
das exakt gleiche, anforderungsfreie Aufgabengebiet (App autonom erkunden und
eine Testsuite erzeugen) — **keiner** von beiden sieht die User-Stories. So misst
der Vergleich rein die Generierungsmethode auf identischer Aufgabe.

**Methode 2 — Anforderungswissen kommt hier rein:** Erst der Hybrid-Refiner
erhält die User-Stories (und optional fachlichen Zusatzkontext) und verbessert
damit `Skript_C`. Hypothese: `Skript_H` schlägt `Skript_C` und `Skript_L`.

> Bewertung: Die gemeinsame Metrik-Suite (inkl. DeepEval-Judge) nutzt die
> User-Stories als **einheitlichen Maßstab für alle drei** Artefakte — auch für
> die story-frei generierten `Skript_C`/`Skript_L`. Das macht die Hybrid-Hypothese
> messbar (hilft injiziertes Anforderungswissen?).

Methode 1 (Crawler + LLM-Agent) ist der lauffähige Kern. Methode 2 (Hybrid)
ist sauber abgegrenzt und wird pro Lauf zugeschaltet, ohne die Baseline zu
verändern.

## Architektur

```
config/            getypte Settings (.env, Präfix TCGEN_) + Ziel-Apps (YAML)
tcgen/
  llm/             Provider-Abstraktion: Ollama (default) | OpenAI
  pipelines/
    crawler/       Zustandsabstraktion, Exploration, Serializer  -> Skript_C
    llm_agent/     Browser-Tools, agentische Exploration, Synthese -> Skript_L
    hybrid/        LLM-Refiner (Methode 2)                       -> Skript_H
  runner/          pytest-Ausführung + Metriken
    metrics/       objective (statisch) | deepeval_judge | iso25010
  orchestration/   Experiment-Runner, Datenmodelle, Results-Store
app/               Streamlit-UI (Mehrseiten)
tests/             Unit-Tests der deterministischen Module
```

Die Provider-Abstraktion ist text-in/text-out. Der Agent nutzt ein portables
JSON-Aktionsprotokoll statt vendor-spezifischem Function-Calling, damit kleine
lokale Ollama-Modelle genauso funktionieren wie gehostete.

## Setup

### 1. Python-Umgebung

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. LLM-Provider

**Ollama (Default, kostenlos, lokal)** — Daemon starten und Modelle ziehen:

```bash
ollama serve &
ollama pull qwen2.5-coder:7b   # Generierung
ollama pull qwen2.5:14b        # Judge (stärkeres Modell empfohlen)
```

**OpenAI (optional)** — in `.env`:

```ini
TCGEN_LLM_PROVIDER=openai
TCGEN_OPENAI_API_KEY=sk-...
```

`.env` aus `.env.example` kopieren und anpassen:

```bash
cp .env.example .env
```

### 3. Ziel-Anwendung

**Empfohlen für den ersten End-to-End-Lauf: OWASP Juice Shop.** Offizielles,
aktiv gepflegtes Image, bootet sofort einsatzbereit (kein Install-Wizard), damit
Läufe reproduzierbar bleiben:

```bash
docker run -d --name juiceshop -p 3000:3000 bkimminich/juice-shop
# SPA unter http://localhost:3000
```

Target: `config/targets/juiceshop.yaml` (Key `juiceshop`).

**OpenCart** — Hinweis: Die früher genutzten Bitnami-Images (`bitnami/opencart`)
wurden im August 2025 nach `bitnamilegacy` verschoben und Ende September 2025
abgeschaltet; `bitnami/opencart` ist nicht mehr ziehbar. Stattdessen ein
gepflegtes Community-Image verwenden, z. B.:

```bash
docker pull webkul/opencart        # oder: aamservices/opencart
```

OpenCart erfordert beim ersten Start i. d. R. den Installations-Wizard; erst
danach ist das Storefront unter der konfigurierten Base-URL erreichbar. Port und
Base-URL ggf. in `config/targets/opencart.yaml` an das gewählte Image anpassen.

Weitere Ziel-Apps (z. B. TodoMVC) als zusätzliche YAML-Dateien im selben Ordner.

## Benutzung

### UI

```bash
streamlit run app/streamlit_app.py
```

- **Experiment starten** — Ziel-App, Pipelines und Bewertung wählen, Lauf ausführen.
- **Ergebnisse** — Vergleichstabelle Metrik × Pipeline, ISO-Aufschlüsselung, Charts.
- **Skripte** — generierte Testskripte ansehen und herunterladen.

### Hintergrund-Läufe & Live-Monitor

Ein Lauf startet als **detachierter Hintergrund-Job** (`tcgen.jobs.worker` als
Subprozess) und läuft weiter, auch wenn du den Tab wechselst oder die Seite
verlässt. Der Live-Monitor zeigt einen Prozent-Fortschritt über alle Pipelines
(Crawler: Zustand x/max, Agent: Schritt x/max, Runner: Lauf x/n, Judge: Metrik
x/4) und streamt die Logzeilen. Über die Job-Auswahl lässt sich ein laufender
Job nach Navigation wieder öffnen. Job-Status/Logs liegen unter
`results/jobs/<job_id>.json` bzw. `.log`.

Worker auch direkt aufrufbar:

```bash
python -m tcgen.jobs.worker <job_id>
```

### Gemeinsames Ausführungs-Harness

Der Runner legt neben jedes generierte Skript eine `conftest.py` (autouse-Fixture),
die für **alle Pipelines einheitlich** gilt — fair, weil Teil der gemeinsamen
Evaluationsumgebung, nicht des Artefakts:

- bounded Per-Action-Timeout (`TCGEN_TEST_ACTION_TIMEOUT_MS`, Default 8000 ms) →
  kaputte/halluzinierte Skripte scheitern schnell statt im 30-s-Default zu hängen;
- automatisches Schließen von Welcome-Dialog/Cookie-Banner nach jeder Navigation
  (sonst fängt das SPA-Modal jeden Klick ab).

SPA-Wartezeiten sind über `TCGEN_SETTLE_TIMEOUT_MS` / `TCGEN_SETTLE_PAUSE_MS`
einstellbar (networkidle gedeckelt, da SPAs wie Juice Shop im Hintergrund pollen).

### Skript-Qualität (methodisch sauber, kein Ergebnis-Schönen)

- **Crawler:** der Serializer nutzt präzise CSS/nth-Selektoren des tatsächlich
  erkundeten Elements (statt `locator(tag).first`), damit `Skript_C` exakt die
  Elemente trifft, die der Crawler angefasst hat.
- **LLM-Agent:** nach der Synthese eine Validierungs-Runde (`compile` + Lint auf
  fehlende `page.`-Präfixe, Explorations-Reste wie `e1`, fehlender Import); bei
  Befund eine einzige Reparatur-Runde (`TCGEN_AGENT_REPAIR`). Macht `Skript_L`
  lauffähig, ohne den Inhalt vorzugeben.
- **Hybrid-Refiner:** muss Navigation/Locator aus `Skript_C` wiederverwenden und
  darf keine App-Selektoren erfinden, die nicht im Eingabeskript vorkommen
  (gegen halluzinierte `.product-card`-artige Selektoren).
- **Komplexität:** `TCGEN_CRAWLER_MAX_ACTIONS_PER_STATE` und
  `TCGEN_CRAWLER_MAX_SCENARIOS` steuern Breite/Anzahl der Szenarien.

### Headless / programmatisch

```python
from tcgen.orchestration.experiment import run_experiment
from tcgen.orchestration.models import Pipeline

rec = run_experiment(
    "juiceshop",
    pipelines=[Pipeline.CRAWLER, Pipeline.LLM_AGENT],
    include_hybrid=True,                 # Methode 2 zuschalten
    domain_context="Fachliche Prüfregeln …",  # optional, nur für den Hybrid-Refiner
)
print(rec.id)
```

## Metriken

**Objektiv (ohne LLM):** Ausführbarkeit, SSR (Successful-Steps-Ratio),
Element-Coverage (distinkte Locator), Flakiness (Outcome-Stabilität über
`flakiness_runs` Wiederholungen), Generierungs- und Laufzeit.

**Semantisch (DeepEval G-Eval, LLM-as-Judge):** Correctness, Appropriateness,
Hallucination, Readability — je [0, 1].

**ISO/IEC 25010 Functional Suitability** (Mapping gemäß SLR §9):
- Functional Correctness ← Judge-Correctness + SSR
- Functional Completeness ← normalisierte Element-Coverage + Ausführbarkeit
- Functional Appropriateness ← Judge-Appropriateness + (1 − Hallucination)

Der `COVERAGE_REFERENCE`-Wert (Normierung der Element-Coverage) ist in
`tcgen/runner/metrics/iso25010.py` dokumentiert und als Threat-to-Validity zu
führen.

## Tests

```bash
pytest          # Unit-Tests der deterministischen Module
```

Verifiziert ohne Live-Stack: Locator-Rendering, URL-Normalisierung,
State-Signaturen, Serializer-Codegen (erzeugtes Skript_C kompiliert),
objektive Metriken, ISO-Mapping, Results-Store-Roundtrip und die
Lazy-Import-Grenzen (Kern importiert ohne Playwright/DeepEval/Streamlit).

## Threats to Validity (für die Auswertung)

LLM-Judge-Bias (gleiche Modellfamilie für Generierung und Bewertung vermeiden),
Größe des Skript-Korpus, Coverage-Normierung, Nichtdeterminismus der
LLM-Generierung (Temperatur niedrig, Wiederholungen erwägen).
