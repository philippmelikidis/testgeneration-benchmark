// Endpräsentation — Web-UI-Testfallgenerierung: LLM vs. traditionell
// HHZ · Fricke / Melikidis · 15.07.2026 · Applied Machine Learning
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
const W = 13.3, H = 7.5;

// ---- Palette (topic-informiert: Test/Terminal-Anmutung, kein Business-Blau) ----
const INK = "17202B";      // dunkler Hintergrund (Titel/Sektion/Fazit)
const PAPER = "FFFFFF";    // Inhaltsfolien
const CORAL = "FF5A3C";    // Skript_L (Held-Akzent)
const TEAL  = "1FA88F";    // Skript_H
const AMBER = "E0912F";    // Skript_S
const SLATE = "7A8794";    // Skript_C (traditionell)
const TEXT  = "17202B";
const MUTED = "6B7683";
const LINE  = "E4E7EB";
const INKSOFT = "9AA7B4";  // gedämpfter Text auf dunkel

// Fonts (safe-list): Serif-Titel + Sans-Body + Mono für Code/Chips
const TF = "Cambria";      // Titel
const BF = "Calibri";      // Body
const MF = "Courier New";  // Code/Chips

const PIPE = {
  C: { name: "Skript_C", col: SLATE, tag: "Crawler",        sub: "traditionell" },
  L: { name: "Skript_L", col: CORAL, tag: "LLM-Agent",      sub: "LLM-only" },
  S: { name: "Skript_S", col: AMBER, tag: "LLM-Agent+Story",sub: "LLM-only" },
  H: { name: "Skript_H", col: TEAL,  tag: "Hybrid",         sub: "Aufsatz" },
};

function softShadow() { return { type: "outer", color: "9AA7B4", blur: 9, offset: 3, angle: 90, opacity: 0.28 }; }

// pipeline chip (mono name on a colored rounded rect)
function chip(s, x, y, k, w) {
  const pi = PIPE[k];
  w = w || 1.5;
  s.addShape("roundRect", { x, y, w, h: 0.42, rectRadius: 0.08, fill: { color: pi.col }, line: { type: "none" }, shadow: softShadow() });
  s.addText(pi.name, { x, y, w, h: 0.42, fontFace: MF, fontSize: 13, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
}

function kicker(s, txt, x, y, color) {
  s.addText(txt.toUpperCase(), { x, y, w: 8, h: 0.3, fontFace: MF, fontSize: 11, bold: true, color: color || MUTED, charSpacing: 2, margin: 0 });
}

// ---------------------------------------------------------------- 1  TITEL
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  s.addText("Applied Machine Learning · HHZ · 15.07.2026", { x: 0.7, y: 0.6, w: 9, h: 0.3, fontFace: MF, fontSize: 12, color: INKSOFT, charSpacing: 2 });
  s.addText([
    { text: "Kann eine KI", options: { color: "FFFFFF", breakLine: true } },
    { text: "Web-UI-Tests schreiben?", options: { color: CORAL, breakLine: true } },
  ], { x: 0.66, y: 2.2, w: 9.6, h: 2.1, fontFace: TF, fontSize: 52, bold: true, lineSpacing: 54 });
  s.addText("Ein empirischer Vergleich: LLM-Agent gegen klassischen Crawler bei der automatischen Testfallgenerierung für Web-Oberflächen.",
    { x: 0.7, y: 4.5, w: 8.2, h: 0.9, fontFace: BF, fontSize: 17, color: INKSOFT, lineSpacing: 24 });
  s.addText("Timon Fricke · Philippos Melikidis", { x: 0.7, y: 6.5, w: 8, h: 0.35, fontFace: BF, fontSize: 15, bold: true, color: "FFFFFF" });
  // rechte Motiv-Spalte: die vier Artefakte
  const bx = 10.7, by = 2.35;
  ["C","L","S","H"].forEach((k, i) => {
    const pi = PIPE[k];
    s.addShape("roundRect", { x: bx, y: by + i*0.86, w: 1.9, h: 0.66, rectRadius: 0.1, fill: { color: "1F2A38" }, line: { color: pi.col, width: 1.25 } });
    s.addText(pi.name, { x: bx+0.16, y: by + i*0.86 + 0.06, w: 1.7, h: 0.3, fontFace: MF, fontSize: 13, bold: true, color: pi.col, margin: 0 });
    s.addText(pi.tag, { x: bx+0.16, y: by + i*0.86 + 0.34, w: 1.7, h: 0.26, fontFace: BF, fontSize: 10.5, color: INKSOFT, margin: 0 });
  });
  s.addNotes("Endpräsentation. Kernfrage: schlägt ein LLM-Agent den klassischen Crawler beim automatischen Schreiben von Web-UI-Tests?");
})();

// ---------------------------------------------------------------- 2  PROBLEM
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Das Problem", 0.7, 0.62, CORAL);
  s.addText("UI-Tests von Hand zu schreiben ist teuer — und veraltet schnell.",
    { x: 0.66, y: 1.0, w: 8.5, h: 1.5, fontFace: TF, fontSize: 33, bold: true, color: TEXT, lineSpacing: 38 });
  const rows = [
    ["Aufwändig", "Jeder Klickpfad, jeder Selektor, jede Prüfung — manuell formuliert und gepflegt."],
    ["Brüchig", "Ein umbenannter Button, ein neues Layout — und ganze Test-Suiten brechen."],
    ["Skaliert nicht", "Moderne SPAs (Angular, React) haben hunderte interaktive Elemente pro Seite."],
  ];
  let y = 2.95;
  rows.forEach((r, i) => {
    s.addShape("roundRect", { x: 0.7, y, w: 0.5, h: 0.5, rectRadius: 0.06, fill: { color: "F3F4F6" }, line: { type: "none" } });
    s.addText(String(i+1), { x: 0.7, y, w: 0.5, h: 0.5, fontFace: TF, fontSize: 20, bold: true, color: CORAL, align: "center", valign: "middle", margin: 0 });
    s.addText(r[0], { x: 1.4, y: y-0.04, w: 3.0, h: 0.4, fontFace: BF, fontSize: 17, bold: true, color: TEXT, margin: 0 });
    s.addText(r[1], { x: 4.4, y: y-0.06, w: 5.1, h: 0.6, fontFace: BF, fontSize: 14, color: MUTED, margin: 0, lineSpacing: 18 });
    y += 0.92;
  });
  // rechte Karte: die Idee
  s.addShape("roundRect", { x: 10.15, y: 1.05, w: 2.55, h: 5.4, rectRadius: 0.12, fill: { color: INK }, line: { type: "none" }, shadow: softShadow() });
  s.addText("Die Idee", { x: 10.4, y: 1.35, w: 2.1, h: 0.35, fontFace: MF, fontSize: 12, bold: true, color: CORAL, charSpacing: 1 });
  s.addText("Eine Maschine erkundet die App selbst und erzeugt die Testsuite.",
    { x: 10.4, y: 1.85, w: 2.1, h: 2.0, fontFace: TF, fontSize: 20, bold: true, color: "FFFFFF", lineSpacing: 24 });
  s.addText("Klassisch per Crawler — oder mit einem LLM-Agenten. Was ist besser?",
    { x: 10.4, y: 4.6, w: 2.1, h: 1.6, fontFace: BF, fontSize: 13.5, color: INKSOFT, lineSpacing: 19 });
})();

// ---------------------------------------------------------------- 3  FORSCHUNGSFRAGE (dunkel)
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  kicker(s, "Forschungsfrage", 0.7, 0.7, CORAL);
  s.addText("Zwei Fragen treiben die Arbeit.", { x: 0.66, y: 1.05, w: 11, h: 0.8, fontFace: TF, fontSize: 30, bold: true, color: "FFFFFF" });
  const q = [
    ["01", "Schlägt der LLM-Agent den Crawler?", "Bei identischer, anforderungsfreier Aufgabe — App autonom erkunden und eine Testsuite erzeugen.", CORAL],
    ["02", "Hilft die Kombination?", "Bringt es Vorteile, den LLM-Agenten mit der Karte des Crawlers (Routen + echte Locator) zu erden?", TEAL],
  ];
  let y = 2.5;
  q.forEach((r) => {
    s.addShape("roundRect", { x: 0.7, y, w: 11.9, h: 1.85, rectRadius: 0.1, fill: { color: "1F2A38" }, line: { type: "none" } });
    s.addText(r[0], { x: 1.0, y: y+0.25, w: 1.4, h: 1.3, fontFace: TF, fontSize: 46, bold: true, color: r[3], margin: 0, valign: "middle" });
    s.addText(r[1], { x: 2.7, y: y+0.28, w: 9.5, h: 0.6, fontFace: TF, fontSize: 24, bold: true, color: "FFFFFF", margin: 0 });
    s.addText(r[2], { x: 2.7, y: y+0.95, w: 9.5, h: 0.7, fontFace: BF, fontSize: 15, color: INKSOFT, margin: 0, lineSpacing: 20 });
    y += 2.1;
  });
})();

// ---------------------------------------------------------------- 4  VIER PIPELINES (Erklärer)
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Was wir gebaut haben", 0.7, 0.55, CORAL);
  s.addText("Vier Wege, dieselbe Testsuite zu erzeugen", { x: 0.66, y: 0.9, w: 12, h: 0.7, fontFace: TF, fontSize: 30, bold: true, color: TEXT });
  const cards = [
    ["C", "Ein Crawler klickt die App autonom durch, baut einen Zustandsgraphen und serialisiert ihn zu einem pytest-Skript.", "ohne User-Story"],
    ["L", "Ein LLM-Agent bekommt dieselbe Aufgabe: die App selbst erkunden und eine Testsuite schreiben.", "ohne User-Story"],
    ["S", "Derselbe LLM-Agent — bekommt zusätzlich die User-Stories und testet sie direkt.", "mit User-Story"],
    ["H", "LLM-Agent, geseedet mit der Crawler-Karte (echte Routen + Locator). Erdet die Story-Tests in real existierenden Selektoren.", "mit User-Story"],
  ];
  const cw = 2.92, gap = 0.18, x0 = 0.7, y0 = 1.95, ch = 4.55;
  cards.forEach((c, i) => {
    const x = x0 + i*(cw+gap); const pi = PIPE[c[0]];
    s.addShape("roundRect", { x, y: y0, w: cw, h: ch, rectRadius: 0.1, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    chip(s, x+0.22, y0+0.28, c[0], 1.55);
    s.addText(pi.tag, { x: x+0.22, y: y0+0.86, w: cw-0.44, h: 0.35, fontFace: BF, fontSize: 15, bold: true, color: TEXT, margin: 0 });
    s.addText(pi.sub, { x: x+0.22, y: y0+1.2, w: cw-0.44, h: 0.3, fontFace: MF, fontSize: 10.5, color: pi.col, margin: 0 });
    s.addText(c[1], { x: x+0.22, y: y0+1.62, w: cw-0.44, h: 2.3, fontFace: BF, fontSize: 13, color: MUTED, margin: 0, lineSpacing: 18 });
    s.addText(c[2], { x: x+0.22, y: y0+ch-0.5, w: cw-0.44, h: 0.32, fontFace: MF, fontSize: 10.5, bold: true, color: TEXT, margin: 0 });
  });
  s.addText("Ablation: C vs. L isoliert die Methode · S vs. H isoliert den Nutzen der Crawler-Erdung.",
    { x: 0.7, y: 6.75, w: 12, h: 0.4, fontFace: BF, italic: true, fontSize: 13.5, color: MUTED });
})();

// ---------------------------------------------------------------- 5  ZWEI METHODEN
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Studiendesign", 0.7, 0.6, CORAL);
  s.addText("Anforderungswissen als Trennlinie", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 30, bold: true, color: TEXT });
  // Methode 1
  s.addShape("roundRect", { x: 0.7, y: 2.0, w: 5.85, h: 4.4, rectRadius: 0.12, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
  s.addText("Methode 1", { x: 1.0, y: 2.3, w: 5, h: 0.35, fontFace: MF, fontSize: 12, bold: true, color: SLATE, charSpacing: 1 });
  s.addText("Fairer A/B — ohne Anforderungen", { x: 1.0, y: 2.65, w: 5.2, h: 0.5, fontFace: TF, fontSize: 21, bold: true, color: TEXT });
  s.addText("Crawler und LLM-Agent bekommen exakt dieselbe Aufgabe. Keiner sieht die User-Stories. Gemessen wird rein die Generierungsmethode.",
    { x: 1.0, y: 3.25, w: 5.25, h: 1.3, fontFace: BF, fontSize: 14.5, color: MUTED, lineSpacing: 20 });
  chip(s, 1.0, 4.9, "C", 1.55); chip(s, 2.75, 4.9, "L", 1.55);
  s.addText("vs.", { x: 4.45, y: 4.9, w: 0.5, h: 0.42, fontFace: TF, fontSize: 16, italic: true, bold: true, color: MUTED, align: "center", valign: "middle", margin: 0 });
  // Methode 2
  s.addShape("roundRect", { x: 6.75, y: 2.0, w: 5.85, h: 4.4, rectRadius: 0.12, fill: { color: INK }, line: { type: "none" }, shadow: softShadow() });
  s.addText("Methode 2", { x: 7.05, y: 2.3, w: 5, h: 0.35, fontFace: MF, fontSize: 12, bold: true, color: TEAL, charSpacing: 1 });
  s.addText("Hybrid — Erdung trifft Story", { x: 7.05, y: 2.65, w: 5.2, h: 0.5, fontFace: TF, fontSize: 21, bold: true, color: "FFFFFF" });
  s.addText("Der Hybrid ist ein live explorierender LLM-Agent (wie S), zusätzlich geseedet mit der Crawler-Karte: entdeckte Routen und echte, verifizierte Locator aus Skript_C.",
    { x: 7.05, y: 3.25, w: 5.25, h: 1.5, fontFace: BF, fontSize: 14.5, color: INKSOFT, lineSpacing: 20 });
  chip(s, 7.05, 4.95, "H", 1.55);
  s.addText("Hypothese: H schlägt C und L.", { x: 8.75, y: 4.95, w: 3.6, h: 0.42, fontFace: BF, fontSize: 14, italic: true, bold: true, color: "FFFFFF", valign: "middle", margin: 0 });
  s.addText("Bewertung: C/L intrinsisch (sahen keine Stories) · S/H story-bewusst.", { x: 0.7, y: 6.75, w: 12, h: 0.4, fontFace: BF, italic: true, fontSize: 13.5, color: MUTED });
})();

// ---------------------------------------------------------------- 6  ARCHITEKTUR
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Architektur", 0.7, 0.55, CORAL);
  s.addText("Ein Rahmen, drei Generatoren, eine Messung", { x: 0.66, y: 0.9, w: 12, h: 0.7, fontFace: TF, fontSize: 29, bold: true, color: TEXT });
  // Stufe 1: Ziel-App
  const box = (x,y,w,h,fill,line) => s.addShape("roundRect", { x,y,w,h, rectRadius: 0.09, fill: { color: fill }, line: line ? { color: line, width: 1.25 } : { type: "none" }, shadow: softShadow() });
  const lab = (t,x,y,w,c,sz,f) => s.addText(t, { x,y,w, h: 0.4, fontFace: f||BF, fontSize: sz||13, bold: true, color: c, align: "center", valign: "middle", margin: 0 });
  box(0.7, 2.3, 2.1, 1.9, INK);
  s.addText("Ziel-App", { x: 0.7, y: 2.55, w: 2.1, h: 0.4, fontFace: TF, fontSize: 18, bold: true, color: "FFFFFF", align: "center", margin: 0 });
  s.addText("OWASP\nJuice Shop", { x: 0.7, y: 3.05, w: 2.1, h: 0.9, fontFace: MF, fontSize: 12, color: INKSOFT, align: "center", margin: 0, lineSpacing: 18 });
  // Stufe 2: drei Pipelines
  const px = 3.55;
  [["C",2.15],["L",3.05],["H",3.95]].forEach(([k,y]) => {
    const pi = PIPE[k];
    box(px, y, 3.0, 0.78, "FBFBFC", pi.col);
    s.addText(pi.name, { x: px+0.18, y: y+0.06, w: 2.7, h: 0.32, fontFace: MF, fontSize: 12.5, bold: true, color: pi.col, margin: 0 });
    s.addText(pi.tag + " · " + pi.sub, { x: px+0.18, y: y+0.4, w: 2.7, h: 0.3, fontFace: BF, fontSize: 11, color: MUTED, margin: 0 });
  });
  s.addText("(S wie L, zusätzlich mit Story)", { x: px, y: 4.82, w: 3.0, h: 0.3, fontFace: BF, italic: true, fontSize: 10.5, color: MUTED, align: "center", margin: 0 });
  // Stufe 3: Runner
  box(6.95, 2.55, 2.35, 1.5, "FBFBFC", LINE);
  s.addText("pytest-\nAusführung", { x: 6.95, y: 2.75, w: 2.35, h: 0.9, fontFace: TF, fontSize: 17, bold: true, color: TEXT, align: "center", margin: 0, lineSpacing: 20 });
  s.addText("+ Execute-verify-repair", { x: 6.95, y: 3.62, w: 2.35, h: 0.3, fontFace: MF, fontSize: 10, color: CORAL, align: "center", margin: 0 });
  // Stufe 4: Metriken -> ISO
  box(9.5, 2.3, 3.1, 1.0, "FBFBFC", LINE);
  s.addText("Metrik-Suite", { x: 9.5, y: 2.42, w: 3.1, h: 0.35, fontFace: TF, fontSize: 16, bold: true, color: TEXT, align: "center", margin: 0 });
  s.addText("objektiv + LLM-as-Judge", { x: 9.5, y: 2.82, w: 3.1, h: 0.3, fontFace: BF, fontSize: 11.5, color: MUTED, align: "center", margin: 0 });
  box(9.5, 3.45, 3.1, 1.0, INK);
  s.addText("ISO/IEC 25010", { x: 9.5, y: 3.57, w: 3.1, h: 0.35, fontFace: TF, fontSize: 16, bold: true, color: TEAL, align: "center", margin: 0 });
  s.addText("Functional Suitability", { x: 9.5, y: 3.97, w: 3.1, h: 0.3, fontFace: BF, fontSize: 11.5, color: INKSOFT, align: "center", margin: 0 });
  // Pfeile
  const arr = (x1,x2,y) => s.addShape("line", { x: x1, y, w: x2-x1, h: 0, line: { color: SLATE, width: 1.75, endArrowType: "triangle" } });
  arr(2.8, 3.5, 3.19); arr(6.55, 6.9, 3.3); arr(9.3, 9.45, 3.3);
  // Footer-Erklärung
  s.addShape("roundRect", { x: 0.7, y: 5.35, w: 11.9, h: 1.35, rectRadius: 0.1, fill: { color: "F3F4F6" }, line: { type: "none" } });
  s.addText([
    { text: "Portables Design.  ", options: { bold: true, color: TEXT } },
    { text: "Provider-Abstraktion (Ollama lokal/Cloud, OpenAI, Gemini) und ein JSON-Aktionsprotokoll statt vendor-spezifischem Function-Calling — kleine lokale Modelle laufen genauso wie gehostete. Der Agent exploriert über den offiziellen Playwright-MCP-Server.", options: { color: MUTED } },
  ], { x: 1.0, y: 5.55, w: 11.3, h: 0.95, fontFace: BF, fontSize: 14, lineSpacing: 20, valign: "middle" });
})();

// ---------------------------------------------------------------- 7  BEWERTUNG
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Wie wir bewerten", 0.7, 0.6, CORAL);
  s.addText("Gemeinsame Metrik-Suite → ISO 25010", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 29, bold: true, color: TEXT });
  // links: zwei Quellen
  const src = [
    ["Objektiv", "aus Ausführung", "Pass-Rate (SSR), ausgeführte Element-Coverage, Flakiness — deterministisch gemessen.", SLATE],
    ["LLM-as-Judge", "DeepEval G-Eval", "Correctness, Appropriateness, Hallucination, Readability — semantisch bewertet.", CORAL],
  ];
  let y = 2.05;
  src.forEach((r) => {
    s.addShape("roundRect", { x: 0.7, y, w: 6.0, h: 2.05, rectRadius: 0.1, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    s.addText(r[0], { x: 1.0, y: y+0.22, w: 4.5, h: 0.4, fontFace: TF, fontSize: 20, bold: true, color: r[3], margin: 0 });
    s.addText(r[1], { x: 1.0, y: y+0.68, w: 5.4, h: 0.3, fontFace: MF, fontSize: 11, color: MUTED, margin: 0 });
    s.addText(r[2], { x: 1.0, y: y+1.02, w: 5.5, h: 0.85, fontFace: BF, fontSize: 13.5, color: MUTED, margin: 0, lineSpacing: 18 });
    y += 2.25;
  });
  // rechts: ISO drei Subcharakteristiken
  s.addShape("roundRect", { x: 7.0, y: 2.05, w: 5.6, h: 4.25, rectRadius: 0.12, fill: { color: INK }, line: { type: "none" }, shadow: softShadow() });
  s.addText("Functional Suitability", { x: 7.3, y: 2.32, w: 5, h: 0.4, fontFace: TF, fontSize: 20, bold: true, color: "FFFFFF" });
  s.addText("drei Subcharakteristiken — einzeln berichtet (ISO 25023), kein Gesamtscore", { x: 7.3, y: 2.78, w: 5, h: 0.3, fontFace: BF, fontSize: 12.5, color: INKSOFT });
  const iso = [
    ["Correctness", "Halten die Prüfungen? (Pass-Rate + Judge)"],
    ["Completeness", "Wie viel der geforderten Stories wird verifiziert?"],
    ["Appropriateness", "Robuste, benutzerorientierte Locator & Prüfungen?"],
  ];
  let yy = 3.35;
  iso.forEach((r) => {
    s.addShape("roundRect", { x: 7.3, y: yy, w: 5.0, h: 0.86, rectRadius: 0.07, fill: { color: "1F2A38" }, line: { type: "none" } });
    s.addText(r[0], { x: 7.5, y: yy+0.1, w: 4.6, h: 0.32, fontFace: BF, fontSize: 15, bold: true, color: TEAL, margin: 0 });
    s.addText(r[1], { x: 7.5, y: yy+0.44, w: 4.6, h: 0.32, fontFace: BF, fontSize: 12, color: INKSOFT, margin: 0 });
    yy += 0.96;
  });
  s.addText("Die Stories dienen als einheitlicher Maßstab für alle vier Artefakte — auch für die story-frei erzeugten.",
    { x: 0.7, y: 6.7, w: 12, h: 0.4, fontFace: BF, italic: true, fontSize: 13.5, color: MUTED });
})();

// ---------------------------------------------------------------- 8  ZIEL-ANWENDUNG
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Die Ziel-Anwendung", 0.7, 0.6, CORAL);
  s.addText("OWASP Juice Shop als Prüfstand", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 29, bold: true, color: TEXT });
  // links: App-Fakten
  s.addShape("roundRect", { x: 0.7, y: 2.0, w: 6.7, h: 4.35, rectRadius: 0.12, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
  s.addShape("ellipse", { x: 1.1, y: 2.45, w: 0.42, h: 0.42, fill: { color: CORAL }, line: { type: "none" } });
  s.addText("OWASP Juice Shop", { x: 1.72, y: 2.38, w: 5.3, h: 0.5, fontFace: TF, fontSize: 23, bold: true, color: TEXT, margin: 0, valign: "middle" });
  s.addText("Komplexe Angular-SPA · E-Commerce", { x: 1.1, y: 3.02, w: 6.0, h: 0.3, fontFace: MF, fontSize: 11.5, color: CORAL, margin: 0 });
  s.addText([
    "Login, Registrierung, Suche, Warenkorb, Chatbot",
    "über 200 katalogisierte interaktive Elemente",
    "Dialoge, Overlays, Hash-Routing",
    "50 Wiederholungen je LLM-Pipeline",
  ].map((t, j, arr) => ({ text: t, options: { bullet: { code: "2022", indent: 14 }, color: MUTED, breakLine: j < arr.length-1, paraSpaceAfter: 10 } })),
    { x: 1.1, y: 3.6, w: 5.9, h: 2.6, fontFace: BF, fontSize: 15, lineSpacing: 20, margin: 0 });
  // rechts: warum diese App (INK)
  s.addShape("roundRect", { x: 7.65, y: 2.0, w: 4.95, h: 4.35, rectRadius: 0.12, fill: { color: INK }, line: { type: "none" }, shadow: softShadow() });
  s.addText("Warum diese App", { x: 7.95, y: 2.32, w: 4.4, h: 0.35, fontFace: MF, fontSize: 12, bold: true, color: TEAL, charSpacing: 1 });
  s.addText("Realistische, stateful SPA mit echter Tiefe — Formulare, Menüs, Dialoge, Overlays. Genug Oberfläche, um Crawler und LLM-Agent gleichermaßen zu fordern.",
    { x: 7.95, y: 2.85, w: 4.4, h: 2.0, fontFace: BF, fontSize: 15, color: INKSOFT, margin: 0, lineSpacing: 21 });
  s.addText("Lokal per Docker gehostet — reproduzierbar, offline, ohne Rate-Limits.",
    { x: 7.95, y: 5.4, w: 4.4, h: 0.8, fontFace: BF, italic: true, fontSize: 13.5, color: "FFFFFF", margin: 0, lineSpacing: 19 });
  s.addText("Scope: ausschließlich funktionale UI-Tests — die absichtlichen Schwachstellen der App sind nicht Testgegenstand (keine Security-/Last-/Usability-Tests).",
    { x: 0.7, y: 6.55, w: 12, h: 0.5, fontFace: BF, italic: true, fontSize: 13, color: MUTED, lineSpacing: 17 });
})();

// ---------------------------------------------------------------- 9  LIVE DEMO (dunkel, Sektion)
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  kicker(s, "Jetzt live", 0.7, 2.3, CORAL);
  s.addText("Live-Demo", { x: 0.66, y: 2.7, w: 9, h: 1.2, fontFace: TF, fontSize: 60, bold: true, color: "FFFFFF" });
  s.addText("Streamlit-Oberfläche: Ziel-App wählen → Pipelines laufen lassen → generierte Skripte und Metriken nebeneinander.",
    { x: 0.7, y: 4.2, w: 8.4, h: 0.9, fontFace: BF, fontSize: 17, color: INKSOFT, lineSpacing: 24 });
  const steps = ["Experiment starten", "Skripte vergleichen", "Ergebnisse lesen"];
  steps.forEach((t, i) => {
    const x = 0.7 + i*4.1;
    s.addShape("roundRect", { x, y: 5.6, w: 3.8, h: 0.95, rectRadius: 0.1, fill: { color: "1F2A38" }, line: { color: CORAL, width: 1 } });
    s.addText("0"+(i+1), { x: x+0.2, y: 5.72, w: 0.9, h: 0.7, fontFace: TF, fontSize: 28, bold: true, color: CORAL, margin: 0, valign: "middle" });
    s.addText(t, { x: x+1.15, y: 5.72, w: 2.5, h: 0.7, fontFace: BF, fontSize: 14.5, bold: true, color: "FFFFFF", margin: 0, valign: "middle" });
  });
})();

// ---------------------------------------------------------------- 10  CODE-VERGLEICH (eigene Artefakte)
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Was dabei herauskommt", 0.7, 0.55, CORAL);
  s.addText("Gleiche Aktion, sehr unterschiedliche Prüfung", { x: 0.66, y: 0.9, w: 12, h: 0.7, fontFace: TF, fontSize: 28, bold: true, color: TEXT });
  // Crawler-Code
  const codeBox = (x, title, k, code, note) => {
    s.addShape("roundRect", { x, y: 1.95, w: 5.85, h: 4.0, rectRadius: 0.1, fill: { color: "141B24" }, line: { type: "none" }, shadow: softShadow() });
    chip(s, x+0.25, 2.2, k, 1.55);
    s.addText(title, { x: x+1.95, y: 2.2, w: 3.6, h: 0.42, fontFace: BF, fontSize: 13, bold: true, color: INKSOFT, valign: "middle", margin: 0 });
    s.addText(code, { x: x+0.28, y: 2.85, w: 5.3, h: 2.55, fontFace: MF, fontSize: 11.5, color: "E6EAEE", margin: 0, lineSpacing: 16 });
    s.addText(note[0], { x: x+0.28, y: 5.55, w: 5.3, h: 0.3, fontFace: BF, fontSize: 12.5, bold: true, color: note[1], margin: 0 });
  };
  codeBox(0.7, "Juice Shop · „Add to Basket“", "C",
    'page.goto(".../#/")\npage.get_by_role(\n  "button", name="Add to Basket"\n).click()\nexpect(\n  page.locator("body")\n).to_be_attached()',
    ["Klickt — prüft aber nichts Fachliches.", SLATE]);
  codeBox(6.75, "Juice Shop · Produktsuche", "L",
    'page.get_by_role(\n  "button", name="Open search"\n).click()\ninput.fill("Apple")\nexpect(\n  page.get_by_text("Apple Juice (1000ml)")\n).to_be_visible()',
    ["Verifiziert echtes App-Verhalten.", TEAL]);
  s.addText("Der Crawler ist immer grün — weil seine Prüfung („Body existiert“) fast nie fehlschlägt. Das ist der Kern des Ergebnisses.",
    { x: 0.7, y: 6.35, w: 12, h: 0.7, fontFace: BF, italic: true, fontSize: 14, color: MUTED, lineSpacing: 19 });
})();

// ---------------------------------------------------------------- 11  ERGEBNIS JUICE SHOP (Chart)
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Ergebnisse · 50 Wiederholungen", 0.7, 0.55, CORAL);
  s.addText("Juice Shop: drei Subcharakteristiken, ein Muster", { x: 0.66, y: 0.9, w: 8.5, h: 0.7, fontFace: TF, fontSize: 29, bold: true, color: TEXT });
  // ISO 25023 misst nur auf Subcharakteristik-Ebene — kein aggregierter Score.
  s.addChart(p.ChartType.bar, [
    { name: "Skript_L", labels: ["Correctness", "Completeness", "Appropriateness"], values: [0.67, 0.56, 0.89] },
    { name: "Skript_S", labels: ["Correctness", "Completeness", "Appropriateness"], values: [0.67, 0.54, 0.76] },
    { name: "Skript_C", labels: ["Correctness", "Completeness", "Appropriateness"], values: [0.90, 0.50, 0.40] },
    { name: "Skript_H", labels: ["Correctness", "Completeness", "Appropriateness"], values: [0.62, 0.47, 0.71] },
  ], {
    x: 0.7, y: 1.85, w: 7.7, h: 4.9, barDir: "col", chartColors: [CORAL, AMBER, SLATE, TEAL],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 9, dataLabelFontFace: BF, dataLabelColor: TEXT, dataLabelFontBold: true,
    valAxisMinVal: 0, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.2, showValAxisTitle: false,
    catAxisLabelColor: TEXT, catAxisLabelFontSize: 13, catAxisLabelFontBold: true, catAxisLabelFontFace: MF,
    valAxisLabelColor: MUTED, valAxisLabelFontSize: 10, valGridLine: { color: LINE, size: 1 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 11, legendFontFace: MF, legendColor: TEXT,
    showTitle: false, barGapWidthPct: 40,
  });
  // rechte Deutung
  s.addShape("roundRect", { x: 8.75, y: 1.95, w: 3.85, h: 4.7, rectRadius: 0.12, fill: { color: INK }, line: { type: "none" }, shadow: softShadow() });
  s.addText("Ablesbar", { x: 9.05, y: 2.25, w: 3.3, h: 0.35, fontFace: MF, fontSize: 12, bold: true, color: CORAL });
  const pts = [
    ["Kein Gesamtscore", "ISO 25023 misst nur die drei Subcharakteristiken — hier einzeln, ungewichtet."],
    ["Methode 1 · C vs L", "C holt Correctness nur über triviale Grün-Checks; L führt bei Completeness & Appropriateness."],
    ["Methode 2 · S vs H", "Live-DOM (S) vor Crawler-Map (H) in allen drei Dimensionen."],
  ];
  let y = 2.75;
  pts.forEach((r) => {
    s.addText(r[0], { x: 9.05, y, w: 3.3, h: 0.32, fontFace: BF, fontSize: 15, bold: true, color: "FFFFFF", margin: 0 });
    s.addText(r[1], { x: 9.05, y: y+0.33, w: 3.3, h: 0.75, fontFace: BF, fontSize: 12.5, color: INKSOFT, margin: 0, lineSpacing: 17 });
    y += 1.25;
  });
})();

// ---------------------------------------------------------------- 12  METHODE 2: GROUNDING VERSAGT
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Methode 2 · Hybrid im Detail", 0.7, 0.6, CORAL);
  s.addText("Grounding, das nicht greift", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 30, bold: true, color: TEXT });
  const stat = (x, k, big, biglab, small, smalllab, verdict) => {
    const pi = PIPE[k];
    s.addShape("roundRect", { x, y: 2.05, w: 5.85, h: 3.15, rectRadius: 0.12, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    chip(s, x+0.3, 2.32, k, 1.55);
    s.addText(pi.tag, { x: x+1.98, y: 2.32, w: 3.6, h: 0.42, fontFace: BF, fontSize: 14, bold: true, color: TEXT, valign: "middle", margin: 0 });
    s.addText(big, { x: x+0.3, y: 2.95, w: 2.7, h: 1.0, fontFace: TF, fontSize: 54, bold: true, color: pi.col, margin: 0 });
    s.addText(biglab, { x: x+0.3, y: 4.02, w: 2.75, h: 0.3, fontFace: BF, fontSize: 12, color: MUTED, margin: 0 });
    s.addText(small, { x: x+3.2, y: 2.95, w: 2.4, h: 1.0, fontFace: TF, fontSize: 54, bold: true, color: TEXT, margin: 0 });
    s.addText(smalllab, { x: x+3.2, y: 4.02, w: 2.35, h: 0.3, fontFace: BF, fontSize: 12, color: MUTED, margin: 0 });
    s.addText(verdict, { x: x+0.3, y: 4.5, w: 5.25, h: 0.55, fontFace: BF, italic: true, fontSize: 12.5, color: pi.col, margin: 0, lineSpacing: 16 });
  };
  stat(0.7, "S", "0.55", "SSR (Pass-Rate)", "42 s", "Gen-Zeit", "Live-DOM · 3 Seiten beobachtet · vorn in allen drei ISO-Subcharakteristiken.");
  stat(6.75, "H", "0.47", "SSR (Pass-Rate)", "221 s", "Gen-Zeit", "Crawler-Map · nur 1 Seite live · teuerste UND schwächste.");
  s.addShape("roundRect", { x: 0.7, y: 5.5, w: 11.9, h: 1.15, rectRadius: 0.1, fill: { color: INK }, line: { type: "none" } });
  s.addText([
    { text: "Warum H verliert:  ", options: { bold: true, color: TEAL } },
    { text: "H bekommt 212 verifizierte Crawler-Locator — hält sich aber nicht daran und erfindet Namen („Email address“ statt der echten „Text field for the login email“). Grounding wirkt nur als harte Constraint, nicht als bloßer Kontext.", options: { color: "FFFFFF" } },
  ], { x: 1.0, y: 5.66, w: 11.3, h: 0.85, fontFace: BF, fontSize: 13.5, lineSpacing: 18, valign: "middle" });
  s.addText("Zahlen: Juice Shop, 50 Wiederholungen.", { x: 0.7, y: 6.78, w: 6, h: 0.3, fontFace: BF, fontSize: 11, italic: true, color: MUTED });
})();

// ---------------------------------------------------------------- 13  DER TRADE-OFF
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Die entscheidende Nuance", 0.7, 0.6, CORAL);
  s.addText("100 % grün heißt nicht: gute Tests", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 30, bold: true, color: TEXT });
  // zwei große Stat-Blöcke (Juice Shop)
  const stat = (x, k, big, biglab, small, smalllab, verdict) => {
    const pi = PIPE[k];
    s.addShape("roundRect", { x, y: 2.05, w: 5.85, h: 3.15, rectRadius: 0.12, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    chip(s, x+0.3, 2.32, k, 1.55);
    s.addText(pi.tag, { x: x+1.98, y: 2.32, w: 3.6, h: 0.42, fontFace: BF, fontSize: 14, bold: true, color: TEXT, valign: "middle", margin: 0 });
    s.addText(big, { x: x+0.3, y: 2.95, w: 2.7, h: 1.0, fontFace: TF, fontSize: 58, bold: true, color: pi.col, margin: 0 });
    s.addText(biglab, { x: x+0.3, y: 4.05, w: 2.7, h: 0.3, fontFace: BF, fontSize: 12.5, color: MUTED, margin: 0 });
    s.addText(small, { x: x+3.15, y: 2.95, w: 2.4, h: 1.0, fontFace: TF, fontSize: 58, bold: true, color: TEXT, margin: 0 });
    s.addText(smalllab, { x: x+3.15, y: 4.05, w: 2.5, h: 0.3, fontFace: BF, fontSize: 12.5, color: MUTED, margin: 0 });
    s.addText(verdict, { x: x+0.3, y: 4.55, w: 5.25, h: 0.5, fontFace: BF, italic: true, fontSize: 13, color: pi.col, margin: 0, lineSpacing: 17 });
  };
  stat(0.7, "C", "1.00", "Pass-Rate (SSR)", "0.40", "Appropriateness", "Immer grün — aber die Prüfungen sind triviale Smoke-Checks.");
  stat(6.75, "L", "0.52", "Pass-Rate (SSR)", "0.89", "Appropriateness", "Seltener grün — aber echte, robuste, benutzerorientierte Tests.");
  s.addShape("roundRect", { x: 0.7, y: 5.5, w: 11.9, h: 1.15, rectRadius: 0.1, fill: { color: INK }, line: { type: "none" } });
  s.addText([
    { text: "Kernpunkt:  ", options: { bold: true, color: CORAL } },
    { text: "Die Pass-Rate allein täuscht. Der Crawler besteht, weil er kaum etwas prüft; der LLM-Agent riskiert Fehlschläge, weil er echtes Verhalten verifiziert. Erst die ISO-Bewertung macht diesen Unterschied sichtbar.", options: { color: "FFFFFF" } },
  ], { x: 1.0, y: 5.68, w: 11.3, h: 0.8, fontFace: BF, fontSize: 14.5, lineSpacing: 20, valign: "middle" });
  s.addText("Zahlen: Juice Shop, 50 Wiederholungen.", { x: 0.7, y: 6.78, w: 6, h: 0.3, fontFace: BF, fontSize: 11, italic: true, color: MUTED });
})();

// ---------------------------------------------------------------- 14  KERNBEFUNDE (dunkel)
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  kicker(s, "Kernbefunde", 0.7, 0.62, CORAL);
  s.addText("Drei belastbare Aussagen", { x: 0.66, y: 1.0, w: 11, h: 0.7, fontFace: TF, fontSize: 30, bold: true, color: "FFFFFF" });
  const f = [
    ["Live schlägt statisch", "Beide Methoden-Duelle gehen an die live erkundenden Agenten: L > C (Methode 1), S > H (Methode 2).", CORAL],
    ["„Grün“ ist nicht „gut“", "Der Crawler ist zu 100 % grün — über leere Smoke-Prüfungen. Pass-Rate und Assertion-Stärke immer zusammen lesen.", AMBER],
    ["Grounding braucht Enforcement", "Die Crawler-Karte hilft nur, wenn sie die Locator-Wahl hart erzwingt. Als bloßer Kontext ignoriert das Modell sie.", TEAL],
  ];
  let y = 2.15;
  f.forEach((r, i) => {
    s.addShape("roundRect", { x: 0.7, y, w: 11.9, h: 1.4, rectRadius: 0.1, fill: { color: "1F2A38" }, line: { type: "none" } });
    s.addText("0"+(i+1), { x: 1.0, y: y+0.2, w: 1.2, h: 1.0, fontFace: TF, fontSize: 40, bold: true, color: r[2], margin: 0, valign: "middle" });
    s.addText(r[0], { x: 2.4, y: y+0.22, w: 9.8, h: 0.5, fontFace: TF, fontSize: 23, bold: true, color: "FFFFFF", margin: 0 });
    s.addText(r[1], { x: 2.4, y: y+0.75, w: 9.9, h: 0.55, fontFace: BF, fontSize: 14.5, color: INKSOFT, margin: 0, lineSpacing: 19 });
    y += 1.58;
  });
})();

// ---------------------------------------------------------------- 15  GRENZEN
(() => {
  const s = p.addSlide(); s.background = { color: PAPER };
  kicker(s, "Ehrliche Grenzen", 0.7, 0.6, CORAL);
  s.addText("Was diese Zahlen nicht sagen", { x: 0.66, y: 0.95, w: 12, h: 0.7, fontFace: TF, fontSize: 29, bold: true, color: TEXT });
  const lim = [
    ["Hohe Streuung", "Trotz 50 Wiederholungen sind die LLM-Läufe verrauscht (Std bis ±0.19). Kleine Abstände sind nicht signifikant."],
    ["Ein Modell", "Nur kimi-k2.7 als Generator, glm-5.2 als Judge. Andere Modelle können die Reihenfolge verschieben."],
    ["LLM-as-Judge", "Die semantische Bewertung ist selbst ein (stochastisches) LLM — kein objektiver Goldstandard."],
    ["Eine App", "Getestet auf OWASP Juice Shop — die Breite realer Web-Apps ist damit noch nicht abgedeckt."],
  ];
  const cw = 5.85, ch = 1.75;
  lim.forEach((r, i) => {
    const x = 0.7 + (i%2)*6.05, y = 2.0 + Math.floor(i/2)*2.0;
    s.addShape("roundRect", { x, y, w: cw, h: ch, rectRadius: 0.1, fill: { color: "FBFBFC" }, line: { color: LINE, width: 1 }, shadow: softShadow() });
    s.addText(r[0], { x: x+0.35, y: y+0.25, w: cw-0.7, h: 0.4, fontFace: TF, fontSize: 19, bold: true, color: CORAL, margin: 0 });
    s.addText(r[1], { x: x+0.35, y: y+0.72, w: cw-0.7, h: 0.9, fontFace: BF, fontSize: 14, color: MUTED, margin: 0, lineSpacing: 19 });
  });
  s.addText("Wir berichten Mittelwerte ± Standardabweichung — und nennen den robusten Kern (L ≥ C) getrennt von unentschiedenen Details.",
    { x: 0.7, y: 6.4, w: 12, h: 0.5, fontFace: BF, italic: true, fontSize: 13.5, color: MUTED });
})();

// ---------------------------------------------------------------- 16  FAZIT (dunkel)
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  kicker(s, "Bedeutung", 0.7, 0.7, CORAL);
  s.addText([
    { text: "LLM-Agenten sind eine ernstzunehmende, ", options: { color: "FFFFFF" } },
    { text: "qualitativ höherwertige", options: { color: CORAL } },
    { text: " Alternative zum klassischen Crawler.", options: { color: "FFFFFF" } },
  ], { x: 0.66, y: 1.3, w: 12, h: 1.8, fontFace: TF, fontSize: 34, bold: true, lineSpacing: 42 });
  const take = [
    ["Für die Praxis", "Wer aussagekräftige UI-Tests will, fährt mit dem LLM-Agenten besser — auch bei etwas mehr Flakiness."],
    ["Für die Methode", "Erdung über eine Crawler-Karte war hier kein Hebel. Der Agent explorierte selbst gut genug."],
    ["Für die Messung", "Pass-Rate allein ist irreführend. Erst eine mehrdimensionale, ISO-basierte Bewertung zeigt die Wahrheit."],
  ];
  let y = 3.45;
  take.forEach((r) => {
    s.addText(r[0], { x: 0.7, y, w: 3.4, h: 0.9, fontFace: MF, fontSize: 13, bold: true, color: TEAL, margin: 0, valign: "top" });
    s.addText(r[1], { x: 4.2, y: y-0.02, w: 8.4, h: 0.9, fontFace: BF, fontSize: 15.5, color: INKSOFT, margin: 0, lineSpacing: 21 });
    y += 1.08;
  });
})();

// ---------------------------------------------------------------- 17  DANKE / Q&A (dunkel)
(() => {
  const s = p.addSlide(); s.background = { color: INK };
  s.addText("Danke.", { x: 0.66, y: 2.5, w: 9, h: 1.2, fontFace: TF, fontSize: 66, bold: true, color: "FFFFFF" });
  s.addText("Fragen & Diskussion", { x: 0.7, y: 3.9, w: 9, h: 0.6, fontFace: BF, fontSize: 22, color: CORAL });
  s.addText("Timon Fricke · Philippos Melikidis   ·   HHZ   ·   pytest · Playwright · ISO/IEC 25010",
    { x: 0.7, y: 6.6, w: 12, h: 0.4, fontFace: MF, fontSize: 12, color: INKSOFT, charSpacing: 1 });
  ["C","L","S","H"].forEach((k, i) => chip(s, 9.7 + (i%2)*1.75, 2.75 + Math.floor(i/2)*0.62, k, 1.6));
})();

p.writeFile({ fileName: "presentation/Endpraesentation_LLM_vs_Crawler.pptx" }).then(f => console.log("WROTE", f));
