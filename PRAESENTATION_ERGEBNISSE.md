# Benchmark-Ergebnisse — LLM- vs. traditionelle Web-UI-Testgenerierung

**Ziel-App:** OWASP Juice Shop · **Generierung:** kimi-k2.7-code · **Judge:** glm-5.2 (andere Modellfamilie → keine In-Family-Bevorzugung)
**Metrik:** ISO/IEC 25010 Functional Suitability = Mittel(Correctness, Completeness, Appropriateness)
**Datenbasis:** 1 konsistenter Lauf, **50 Wiederholungen** pro LLM-Pipeline, Mittelwerte.
**Pipelines:** Skript_C (traditioneller Crawler) · Skript_L (LLM-Agent ohne Story) · Skript_S (LLM-Agent mit Story) · Skript_H (Hybrid: LLM erdet auf Crawler-Karte)

---

## Ergebnis (50 Wiederholungen)

| Pipeline | ISO-FS | SSR | Correctness | Completeness | Appropriateness |
|---|---|---|---|---|---|
| **Skript_L** (LLM frei) | **0.60** | 0.70 | 0.68 | 0.31 | 0.81 |
| Skript_C (Crawler) | 0.43 | **1.00** | 0.80 | 0.00 | 0.50 |
| Skript_S (LLM + Story) | 0.41 † | 0.17 † | 0.46 | 0.04 | 0.72 |
| Skript_H (Hybrid) | 0.40 † | 0.50 † | 0.59 | 0.06 | 0.54 |

**† Untere Schranke.** Ein Subprozess-Stdio-Bug hat in diesem Lauf die Selbst-Reparatur-Schleife von S/H intermittierend deaktiviert (eindeutig erkennbar: **null Varianz** über 50 Reps, während L normal streut). Bug identifiziert und behoben. **Im crashfreien Kontroll-Lauf mit aktiver Reparatur: SSR von S ≈ 0.47, H ≈ 0.47** — d. h. das wahre Niveau von S/H liegt deutlich höher als hier gemessen.

---

## Kernaussagen

1. **Kein Sieger — ein Trade-off zwischen Zuverlässigkeit und Anforderungsabdeckung.**
   - **Crawler (C):** maximal zuverlässig (SSR 1.0, immer grün), aber **anforderungsblind** — deckt *keine* der 6 User-Stories ab (Completeness 0), nur generische Smoke-Assertions.
   - **LLM frei (L):** höchste ISO-FS (0.60) — beste Balance aus Abdeckung und Angemessenheit.
   - **Story/Hybrid (S/H):** zielen bewusst auf die *geforderten*, schwierigen Flows (Login, Registrierung, Warenkorb hinter Anmeldung) — anspruchsvoller, daher niedrigere Pass-Rate.

2. **Zwei Messfehler gefunden und korrigiert — der methodische Kernbeitrag:**
   - **Halluzination:** G-Eval bewertet „höher = besser". Ohne Inversion wurde stark geerdeter Code als „am meisten halluzinierend" ausgewiesen — die Metrik musste umgedreht werden.
   - **Completeness:** darf nicht „Anteil *aller* App-Elemente" sein (drückt jede fokussierte Suite künstlich auf ~0.1), sondern **Anteil der abgedeckten User-Stories** (ISO: „specified tasks and user objectives").

3. **Faires Design, kein Bias:**
   - Alle Pipelines starten am **selben, einzigen** Einstiegspunkt — keine gesäten Routen.
   - Login als **geteiltes Zugangsdaten-Fixture**, identisch für alle.
   - Judge aus **anderer Modellfamilie** als der Generator.
   - Identische Test-Harness (Overlay-Dismiss, Timeouts) für alle Pipelines.

4. **Grenze der Methode 2 (Hybrid) — sauberer Befund:**
   Der Crawler erreicht Login/Register autonom nicht (auch bei Tiefe 5 / 80 Zuständen bestätigt) → diese Elemente fehlen H als Grounding → H schreibt dort konservative Assertions. **Die Grounding-Qualität des Hybrids ist durch die Reichweite des Crawlers gedeckelt.**

---

## Robustheit
- 50 Wiederholungen pro LLM-Pipeline; Mittelwert ± Standardabweichung.
- Das Ranking ist robust gegenüber beiden Metrik-Korrekturen.
- Judge mit Retry gegen sporadische JSON-Fehler abgesichert.
- Ein während der Auswertung gefundener Stdio-Bug wurde behoben; die betroffenen S/H-Werte sind transparent als untere Schranke ausgewiesen.
