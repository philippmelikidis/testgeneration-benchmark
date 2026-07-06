# Faires Vergleichs-Setup — Änderungen & Auswertungsdesign

Ziel: Jede Pipeline soll sich nur noch in ihrer *beabsichtigten* Variable
unterscheiden. Alle beiläufigen Asymmetrien (Test-Granularität, API-Leitplanken,
Repair-Schritt) wurden entfernt bzw. angeglichen.

## 1. Was geändert wurde

### `tcgen/pipelines/llm_agent/prompts.py` (Skript_L und Skript_S)
- **Granularitäts-Vorgabe entfernt.** L: „produce SEVERAL test functions, one per
  distinct flow" → neutral („entscheide Anzahl/Struktur selbst"). S: „one test
  function per user story" → neutral, aber Story-*Verifikation* bleibt erhalten.
  Auch `(one test each)` aus dem User-Prompt und die Hinweise auf
  „story-referencing names" entfernt.
- **API-Whitelist ergänzt** (L und S): explizite Liste der gültigen `expect`-
  Assertions plus „do NOT invent Playwright methods / es gibt kein
  `to_have_count_greater_than`" — identisch zu dem, was H schon hatte.

### `tcgen/pipelines/hybrid/refiner.py` (Skript_H)
- **Granularitäts-Vorgabe entfernt** („one test function per user story" →
  neutral; Story-Verifikation via Katalog bleibt).
- **Repair-Pass ergänzt:** H durchläuft jetzt denselben Validate-+-Repair-
  Crash-Guard wie L/S (Aufruf von `maybe_repair_code` vor dem Postprocess).
- API-Whitelist war bereits vorhanden (unverändert).

### `tcgen/pipelines/llm_agent/agent.py`
- Repair-Logik aus `_maybe_repair` in eine **wiederverwendbare Modul-Funktion
  `maybe_repair_code(code, provider, settings, phase)`** extrahiert. L, S und H
  teilen sich jetzt eine einzige Repair-Implementierung (kein Copy-Paste-Drift).

### Crawler (Skript_C)
- **Unverändert.** Deterministisch → läuft bewusst nur 1×. Bekommt kein
  Varianzband und wird als deterministische Baseline geführt.

**Netto:** Granularität, API-Leitplanken und Repair sind jetzt über alle
LLM-Pipelines gleich. Die verbleibenden Unterschiede sind genau die
Untersuchungsvariablen (siehe unten).

## 2. Verbleibende (gewollte) Unterschiede

| Pipeline | Methode | Stories? | Grounding-Quelle | Judge-Rubrik |
|---|---|---|---|---|
| Skript_C | 1 (req.-frei) | nein | deterministischer Crawl | intrinsisch |
| Skript_L | 1 (req.-frei) | nein | Live-Exploration (LLM) | intrinsisch |
| Skript_S | 2 (story) | ja | Live-Exploration (LLM) | story-aware |
| Skript_H | 2 (story) | ja | Crawler-Map (Refiner) | story-aware |

Die Judge-Rubrik hängt an der **Methode**, nicht an der einzelnen Pipeline —
das ist Absicht und bleibt so.

## 3. Wie wir vergleichen sollten

### Vergleich A — Skript_C vs Skript_L  (innerhalb Methode 1)
- **Frage:** Traditioneller Crawler vs. LLM-Agent bei identischer, requirement-
  freier Aufgabe.
- **Rubrik:** beide intrinsisch → **alle** Kennzahlen vergleichbar (SSR,
  Completeness, Judge-Correctness/Appropriateness/Readability).
- **Caveats:** C ist deterministisch/1× (kein Varianzband); Hallucination nur
  für L (bei C n/a).

### Vergleich B — Skript_S vs Skript_H  (innerhalb Methode 2)
- **Frage:** Grounding via Live-Exploration (S) vs. via Crawler-Map (H).
- **Rubrik:** beide story-aware → **alle** Kennzahlen vergleichbar.
- **Jetzt sauber isoliert:** Granularität, API-Whitelist und Repair sind
  angeglichen; einzige verbleibende Variable ist die Grounding-Quelle.

### Vergleich C — alle vier nach SSR (+ vorsichtig Completeness)
- **SSR** ist die einzige echte methodenneutrale Achse (rein ausführungsbasiert,
  keine Rubrik). Nach der Granularitäts-Angleichung fair über alle vier.
- **Completeness** ist neutral gerechnet, aber *breiten-verzerrt* (misst gegen
  die volle Crawler-Oberfläche) → am aussagekräftigsten bei gleicher Zielbreite
  (also L↔C); für S/H nur mit diesem Vorbehalt lesen.

### Zusatz — Skript_L vs Skript_S  (Story-Effekt, kreuzt Methoden)
- Isoliert generierungsseitig sauber den Story-Effekt (gleiche Klasse, gleiche
  Live-Exploration, ± Story).
- **Aber:** L wird intrinsisch, S story-aware bewertet → **Judge-Scores sind
  hier NICHT vergleichbar.** Nur die ausführungsbasierten Achsen (SSR, #Tests,
  Completeness) sind für L vs S aussagekräftig.

## 4. Faustregel für die Metriken

- **Judge-basiert** (Correctness, Appropriateness, Hallucination, Readability)
  und damit auch **Functional Suitability**: nur **innerhalb** einer Methode
  vergleichen (C↔L oder S↔H). Niemals Methode 1 gegen Methode 2.
- **SSR:** über alle vier vergleichbar.
- **Completeness:** neutral gerechnet, aber nur bei gleicher Zielbreite fair.

Kurz: zwei saubere In-Methoden-Vergleiche (C vs L, S vs H) mit *allen*
Kennzahlen, plus ein methodenübergreifendes SSR-Ranking über alle vier.
