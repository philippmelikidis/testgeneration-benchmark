# Web-UI Testfallgenerierung — LLM vs. traditionell

Empirische Werkbank zum Methodenentwurf (Fricke / Melikidis, HS Reutlingen).
Drei Generierungs-Pipelines auf denselben Ziel-Anwendungen, bewertet durch eine
gemeinsame Metrik-Suite und auf ISO/IEC 25010 *Functional Suitability* abgebildet.
User-Stories steuern Methode 2 und dienen als gemeinsamer Bewertungsmaßstab
(siehe unten).

| Pipeline | Artefakt | Methode | Kurz |
|----------|----------|---------|------|
| Crawler       | `Skript_C` | traditionell | autonomer Playwright-Crawler, Zustandsgraph → pytest-Skript; **ohne** User-Story |
| LLM-Agent     | `Skript_L` | LLM-only     | gleiche Aufgabe wie der Crawler (App autonom erkunden, Testsuite erzeugen); **ohne** User-Story |
| LLM-Agent+Story | `Skript_S` | LLM-only   | LLM-Agent erkundet die App **und** bekommt die User-Stories → testet sie direkt |
| Hybrid        | `Skript_H` | Aufsatz      | **Grounded-Agent**: erkundet die App **live** wie `Skript_S`, ist aber mit der **Crawler-Map** (entdeckte Routen + echte, verifizierte Locator aus `Skript_C`) geseedet — navigiert damit gezielt (z. B. zu Login/Register) und erdet die Story-Testsuite in realen Selektoren statt erfundener |

Ablation: `Skript_L` vs. `Skript_S` isoliert den Effekt der Anforderungen beim
LLM-Agenten; `Skript_S` vs. `Skript_H` vergleicht „LLM erkundet selbst mit Story"
gegen „LLM nutzt die geerdete Crawler-Map mit Story". Bewertung: C/L intrinsisch
(sahen keine Stories), S/H story-bewusst.

**Methode 1 — fairer A/B ohne Anforderungen:** Crawler und LLM-Agent bekommen
das exakt gleiche, anforderungsfreie Aufgabengebiet (App autonom erkunden und
eine Testsuite erzeugen) — **keiner** von beiden sieht die User-Stories. So misst
der Vergleich rein die Generierungsmethode auf identischer Aufgabe.

**Methode 2 — Anforderungswissen kommt hier rein:** Der Hybrid ist ein **live
explorierender LLM-Agent** (wie `Skript_S`), zusätzlich geseedet mit der
Crawler-Map (entdeckte Routen + echte, verifizierte Locator aus `Skript_C`). Er
klickt selbst durch, verifiziert Elemente am lebenden DOM und erdet die
Story-Testsuite in realen, vom Crawler bestätigten Selektoren. Hypothese:
`Skript_H` schlägt `Skript_C` und `Skript_L`.

**Execute-verify-repair (alle LLM-Pipelines):** Nach der Synthese wird jede
LLM-Suite ausgeführt; jeder rote Test wird mit seinem echten Playwright-Fehler
ans Modell zurückgegeben, gezielt korrigiert und erneut ausgeführt (beste
Pass-Rate gewinnt). Identisch für L/S/H; der deterministische Crawler ist
ausgenommen. So schreiben die LLMs Tests iterativ — wie ein Entwickler — statt
blind in einem Zug.

> Bewertung: Die gemeinsame Metrik-Suite (inkl. DeepEval-Judge) nutzt die
> User-Stories als **einheitlichen Maßstab für alle drei** Artefakte — auch für
> die story-frei generierten `Skript_C`/`Skript_L`. Das macht die Hybrid-Hypothese
> messbar (hilft injiziertes Anforderungswissen?).

Methode 1 (Crawler + LLM-Agent) ist der lauffähige Kern. Methode 2 (Hybrid)
ist sauber abgegrenzt und wird pro Lauf zugeschaltet, ohne die Baseline zu
verändern.

## Eingrenzung (Scope)

Was der Benchmark misst — und was bewusst **nicht**:

- **Nur funktionale UI-Tests.** Alle Pipelines erzeugen End-to-End-Tests auf
  UI-Ebene (Playwright, black-box). **Keine** Penetration-/Security-Tests
  (Juice Shops absichtliche Schwachstellen sind nicht Testgegenstand), keine
  Last-/Performance-Tests, keine Usability-/Accessibility-Prüfungen, keine
  Unit- oder API-Tests.
- **Bewertung ausschließlich ISO/IEC 25010 *Functional Suitability*** — gemessen
  nach ISO/IEC 25023 auf Subcharakteristik-Ebene (Functional Correctness,
  Completeness, Appropriateness), **ohne aggregierten Gesamtwert** (eine
  Verdichtung erforderte begründete Gewichte nach ISO/IEC 25040). Andere
  Qualitätscharakteristiken (Security, Performance Efficiency, Usability,
  Maintainability, …) liegen außerhalb des Scopes.
- **Eine Ziel-Anwendung.** Hauptergebnis auf OWASP Juice Shop (Angular-SPA);
  Generalisierung nur intern angetestet ([reports/](reports/README.md)).
- **Ein Modell-Setup pro Lauf.** Ein Generierungs- und ein Judge-Modell —
  der Benchmark vergleicht *Generierungsmethoden*, nicht LLMs untereinander.
- **Sechs User Stories** als Anforderungsbasis (Methode 2 und Bewertungs-
  maßstab) — kein Anspruch auf vollständige fachliche Abdeckung der App.
- **LLM-as-Judge statt menschlicher Ground-Truth.** Die semantischen Metriken
  (G-Eval) sind modellbasiert; objektive Metriken (SSR, Coverage) gleichen das
  teilweise aus.
- **Nicht-Determinismus wird statistisch behandelt** (50 Wiederholungen,
  Mittelwert ± Standardabweichung), nicht eliminiert.
- **Momentaufnahme der Generierung.** Wartbarkeit, Test-Evolution und
  Flakiness über Zeit/CI sind nicht Teil der Untersuchung.

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

**Agent-Browser-Backend.** Der LLM-Agent exploriert standardmäßig über den
**offiziellen Playwright-MCP-Server** (`@playwright/mcp`, Microsoft): navigieren/
klicken/tippen über die Standard-MCP-Tools, Beobachtung als
Accessibility-Snapshot (ARIA-Baum mit stabilen `[ref=eNN]`-Referenzen) — ein
stärkeres, realistischeres Grounding als ein selbstgebauter DOM-Harvest. Das
portable JSON-Aktionsprotokoll bleibt erhalten (kein natives Function-Calling
nötig); die Aktionen werden nur auf MCP-Tools übersetzt. Lässt sich der Server
nicht starten (kein Node/npx), fällt der Agent automatisch auf das
In-Process-Playwright-Backend zurück; das tatsächlich genutzte Backend steht in
`script.meta["browser_backend"]`. Umschaltbar über `TCGEN_AGENT_BROWSER_BACKEND`
(`playwright_mcp` | `inprocess`).

## Setup

### 1. Python-Umgebung

**macOS / Linux:**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**Windows (PowerShell):**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

> Windows-Hinweise: In der klassischen `cmd.exe` stattdessen
> `.venv\Scripts\activate.bat` aufrufen. Blockiert PowerShell das Skript
> („running scripts is disabled"), einmalig
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` setzen.

**Node.js 18+ (für das Agent-MCP-Backend).** Der LLM-Agent nutzt standardmäßig
den offiziellen Playwright-MCP-Server, der per `npx @playwright/mcp@latest`
gestartet wird — dafür muss Node.js 18+ (`node`, `npx`) auf dem PATH liegen. Beim
ersten Lauf lädt `npx` das Paket einmalig nach (daher das großzügige Start-
Timeout `TCGEN_PLAYWRIGHT_MCP_START_TIMEOUT_S`). Fehlt Node, fällt der Agent auf
das In-Process-Backend zurück (`TCGEN_AGENT_BROWSER_BACKEND=inprocess` erzwingt
das explizit).

### 2. LLM-Provider

**Ollama (Default, kostenlos, lokal)** — Daemon starten und Modelle ziehen:

```bash
ollama serve &                 # Windows: läuft nach Install als Hintergrund-App
ollama pull qwen2.5-coder:7b   # Generierung
ollama pull qwen2.5:14b        # Judge (stärkeres Modell empfohlen)
```

**Ollama Cloud (gehostet, mit API-Key)** — in `.env`:

```ini
TCGEN_LLM_PROVIDER=ollama
TCGEN_OLLAMA_BASE_URL=https://ollama.com
TCGEN_OLLAMA_API_KEY=...
TCGEN_OLLAMA_MODEL=gpt-oss:120b
TCGEN_OLLAMA_JUDGE_MODEL=gpt-oss:120b
```

Derselbe Provider deckt lokal und Cloud ab: ohne Key → lokaler Daemon, mit Key +
`https://ollama.com` → Cloud (Bearer-Auth, Cloud-Modelle wie `gpt-oss:120b`).

**OpenAI (optional)** — in `.env`:

```ini
TCGEN_LLM_PROVIDER=openai
TCGEN_OPENAI_API_KEY=sk-...
```

**Gemini (optional, schnell, gehostet)** — in `.env`:

```ini
TCGEN_LLM_PROVIDER=gemini
TCGEN_GEMINI_API_KEY=...
TCGEN_GEMINI_MODEL=gemini-2.5-flash
TCGEN_GEMINI_JUDGE_MODEL=gemini-2.5-flash   # oder gemini-2.5-pro für besseren Judge
```

Hinweis: Gemini beschleunigt die LLM-Stufen (Skript_L, Skript_H, Judge) deutlich.
Der **Crawler ist browser-gebunden und wird dadurch nicht schneller** — seine
Laufzeit ist reine Playwright-Exploration ohne LLM.

`.env` aus `.env.example` kopieren und anpassen:

```bash
cp .env.example .env        # macOS / Linux
copy .env.example .env      # Windows
```

### 3. Ziel-Anwendung

**Empfohlen für den ersten End-to-End-Lauf: OWASP Juice Shop.** Offizielles,
aktiv gepflegtes Image, bootet sofort einsatzbereit (kein Install-Wizard), damit
Läufe reproduzierbar bleiben:

```bash
docker run -d --name juiceshop -p 3000:3000 bkimminich/juice-shop
# SPA unter http://localhost:3000
```

Target: `config/targets/juiceshop.yaml` (Key `juiceshop`). Weitere Ziel-Apps
lassen sich als zusätzliche YAML-Dateien im selben Ordner ergänzen.

### 4. Crawler-Backend (optional)

Zwei Backends, per `.env` umschaltbar:

```bash
TCGEN_CRAWLER_BACKEND=bfs       # Default: klick-basierter Explorer (Klick-Pfad-Szenarien)
TCGEN_CRAWLER_BACKEND=crawlee   # crawlee[playwright]: parallele Route-Discovery
```

Für `crawlee` zusätzlich `pip install "crawlee[playwright]"`. Das Route-Discovery-
Backend findet über Links auch tiefe Routen (Login/Register) schneller; `Skript_C`
wird dabei zu Route-Smoke-Tests. `bfs` bleibt der reproduzierbare Default.

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
  Elemente trifft, die der Crawler angefasst hat. Der Crawler **sendet
  Suchfelder ab** (Enter nach dem Tippen), damit Ergebnis-/Detail-/Warenkorb-
  Flows überhaupt erreicht werden, und erfasst neben semantischen Tags auch
  **generische SPA-Klickelemente** (ARIA-Rollen, `tabindex`, `cursor:pointer` —
  z. B. Angular-Material-Produktkarten), die ein reiner `a/button/input`-Harvest
  übersieht. Der Crawler ist die **Vollständigkeits-Baseline**, daher zählt
  Abdeckung vor Tempo: das Wall-Clock-Budget (`TCGEN_CRAWLER_TIME_BUDGET_S`) ist
  **standardmäßig aus (0)**, die Timeouts sind großzügig, damit kein langsam-aber-
  gültiges Element übersprungen wird. Setze ein positives Budget nur, wenn du die
  Laufzeit bewusst deckeln willst.
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

**Objektiv (ohne LLM):**
- **SSR / Pass-Rate** — bestandene Tests ÷ Tests (kontinuierlich).
- **Element-Coverage (genutzt)** — distinkte Locator aus *bestandenen* Tests.
  Execution-gated, damit halluzinierte Locator (in fehlschlagenden Tests) den
  Wert nicht aufblähen. Die statische Variante (alle Code-Locator) wird nur als
  Referenz mitgeführt.
- **Flakiness** — Outcome-Stabilität über `flakiness_runs` Wiederholungen.
- Generierungs- und Laufzeit.

**Semantisch (DeepEval G-Eval, LLM-as-Judge):** Correctness, Appropriateness,
Hallucination, Readability — je [0, 1].

**ISO/IEC 25010 Functional Suitability** (Mapping gemäß SLR §9):
- Functional Correctness ← mean(Judge-Correctness, Pass-Rate) — Pass-Rate
  **kontinuierlich**, kein binäres „ausführbar".
- Functional Completeness ← **Anteil der abgedeckten User-Stories** (ISO:
  „covers all specified tasks and user objectives"). Eine Story gilt als abgedeckt,
  wenn ein **bestandener** Test ihre Signatur-Elemente referenziert (pro Story in
  der Ziel-YAML als `key_elements` hinterlegt — transparent, für alle Pipelines
  identisch). Das löst den früheren „Anteil-aller-App-Elemente"-Nenner ab, der
  fokussierte Story-Suiten strukturell auf ~0.1 drückte. Fallback (nur ohne
  Story-Signaturen): genutzte Element-Coverage ÷ distinkte Crawler-Affordances.
- Functional Appropriateness ← Judge-Appropriateness (für alle Pipelines gleich).
  Hallucination ist eine **eigenständige** Metrik (nicht in ISO eingerechnet) und
  beim Crawler **n/a** — strukturell nicht anwendbar, da er nur real erkundete
  Elemente serialisiert. So verändert ein n/a-Wert die ISO-Vergleichbarkeit nicht.

**Interpretation (wichtig) — entkoppelte Judge-Bewertung:** Der Judge bewertet
jede Pipeline mit dem zu ihrer Aufgabe passenden Maßstab:
- `Skript_C` / `Skript_L` (Methode 1, ohne Stories generiert) werden
  **intrinsisch** bewertet: kohärente Aktionen/Assertions, robuste Locator,
  Lesbarkeit; Hallucination = Bezug auf Elemente, die für die App *unplausibel*
  sind — **nicht** „nicht in den Stories".
- `Skript_H` (Methode 2) wird **gegen die User-Stories** bewertet
  (Akzeptanzkriterien-Abdeckung).

Dadurch wird ein echter Crawler nicht mehr fälschlich als „100% Hallucination"
gewertet, nur weil er reale, aber nicht-in-Stories-stehende Elemente testet.
Folge: Judge-Zahlen sind je Methode fair, aber zwischen Methode 1 und 2 nur
eingeschränkt direkt vergleichbar — beim Reporten so benennen. Der
Completeness-Nenner ist seit der Entkopplung die Union der real ausgeführten
Locator aller Pipelines; der Restbias liegt jetzt darin, dass nur *bestandene*
Tests zählen (eine Pipeline kann eine Oberfläche erreichen, aber durch einen
fehlschlagenden Test nicht „verifizieren") — beim Reporten erwähnen.

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

## Artefakte

- `presentation/Endpraesentation_LLM_vs_Crawler_v2.pptx` — Endpräsentation
  (finale, manuell überarbeitete Fassung; `presentation/build_deck.js` ist der
  ursprüngliche Generator der Basis-Version).
- `Planning_SLR.pdf` — Systematic Literature Review, auf dem das Metrik-Mapping
  (ISO/IEC 25010) beruht.
- `reports/` — kuratierte Ergebnisberichte als Verlauf (frühe Baseline → finaler
  Referenzlauf, inkl. TodoMVC-Generalisierung); siehe [`reports/README.md`](reports/README.md).
- `results/` — die zu den Berichten gehörenden **Roh-Records** (JSON) zum direkten
  Herunterladen und erneuten Auswerten im UI/CLI:
  - [`results/20260707-212947_juiceshop_25a1d1.json`](results/20260707-212947_juiceshop_25a1d1.json) — frühe Baseline (Bericht 01)
  - [`results/20260709-214648_juiceshop_d66cf0.json`](results/20260709-214648_juiceshop_d66cf0.json) — finaler Referenzlauf (Bericht 02)
  - [`results/20260710-082622_todomvc_515845.json`](results/20260710-082622_todomvc_515845.json) — Generalisierung (Bericht 03)

Nur diese drei Records sind bewusst eingecheckt. Die übrigen Rohdaten der Läufe
(`results/*.json`), generierte Skripte (`generated/`) und Crawlee-Scratch
(`storage/`) bleiben **nicht** eingecheckt — sie entstehen reproduzierbar beim
Ausführen.
