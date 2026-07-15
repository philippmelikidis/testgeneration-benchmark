# Ergebnisberichte (Verlauf)

Kuratierte Roh-Ergebnisberichte aus dem Benchmark — als **Verlauf** von der frühen
Baseline bis zum finalen Referenzlauf. Jeder Bericht ist reproduzierbar aus dem
zugehörigen JSON-Record generiert (`tcgen.orchestration.report.record_to_markdown`)
und enthält Metriken **plus** die tatsächlich generierten Test-Skripte je Pipeline
(C = Crawler, L = LLM-Agent, S = LLM-Agent + Story, H = Hybrid).

| Bericht | App | Reps | Stand | Rolle |
|---|---|---|---|---|
| [01_juiceshop_50reps_fruehe_baseline.md](01_juiceshop_50reps_fruehe_baseline.md) | Juice Shop | 50 | 07.07. | Frühe Baseline — vor Backdrop-/Prompt-/Story-Fixes (Hybrid noch schwach, H≈0.38) |
| [02_juiceshop_50reps_final.md](02_juiceshop_50reps_final.md) | Juice Shop | 50 | 09.07. | **Finaler Referenzlauf** — Hauptergebnis der Auswertung |
| [02_juiceshop_50reps_final_vergleich.html](02_juiceshop_50reps_final_vergleich.html) | Juice Shop | 50 | 09.07. | Visueller Vergleich zum finalen Lauf (im Browser öffnen) |
| [03_todomvc_50reps_generalisierung.md](03_todomvc_50reps_generalisierung.md) | TodoMVC | 50 | 10.07. | Interner Generalisierungstest auf einer zweiten App |

## Lesehilfe

- **ISO/IEC 25010 Functional Suitability** (Correctness, Completeness, Appropriateness)
  ist die zentrale Qualitätsdimension; Werte in `[0,1]`, höher = besser.
- **SSR** (Self-Consistency / Pass-Rate) misst, ob die generierten Tests grün laufen —
  ein hoher SSR bei niedriger Suitability bedeutet „grün, aber wenig geprüft".
- Der Verlauf zeigt die Wirkung der Fixes: zwischen `01` und `02` wurden u. a. der
  CDK-Backdrop-Bug, die Prompt-Fidelity-Regeln und die Story-Anbindung (S/H) korrigiert.
- **TodoMVC** (`03`) war ein interner Generalisierungstest auf einer zweiten,
  bewusst simplen App und ist **nicht** Teil des gepflegten Target-Setups —
  der Bericht bleibt hier nur als historischer Beleg erhalten.

> Die belastbaren Zahlen der Endpräsentation beziehen sich auf den **finalen
> Juice-Shop-Lauf (`02`)**. Die 5-Rep-Zwischenläufe der Entwicklung sind bewusst
> nicht abgelegt (zu hohe Varianz für belastbare Aussagen).
