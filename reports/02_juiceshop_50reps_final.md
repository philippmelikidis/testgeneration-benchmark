> **Finaler Juice-Shop-Referenzlauf (50 Reps) — Hauptergebnis**
>
> Teil des Ergebnis-Verlaufs. Roh-Record: `20260709-214648_juiceshop_d66cf0`.

# Ergebnisbericht — OWASP Juice Shop

- Experiment: `20260709-214648_juiceshop_d66cf0`
- Provider / Modell: `ollama` / `kimi-k2.7-code:cloud`
- Zeitpunkt: 2026-07-09T21:46:48+00:00
- Notes: coverage_denominator=207 (crawler_affordances) repetitions=50 judge_model=glm-5.2:cloud judge_in_family=False stories=['US-1', 'US-2', 'US-3', 'US-5', 'US-6', 'US-7']

## Vergleichstabelle — Metrik × Pipeline

| Metrik | Skript_C | Skript_L | Skript_S | Skript_H |
|---|---|---|---|---|
| Gen-Zeit (s) (↓) | 185.010 | 57.840 ± 130.506 | 42.090 ± 73.611 | 221.120 ± 73.752 |
| Ausführbar (↑) | ja | ja | ja | ja |
| Alle Tests grün (↑) | ja | nein | nein | nein |
| # Tests | 30 | 11 ± 1.785 | 6 | 6 |
| SSR (Pass-Rate) (↑) | 1.000 | 0.523 ± 0.174 | 0.550 ± 0.162 | 0.470 ± 0.190 |
| Element-Coverage (genutzt) (↑) | 32 | 21 ± 6.723 | 14 ± 3.664 | 11 ± 4.599 |
| Element-Coverage (statisch) | 32 | 37 ± 4.851 | 20 ± 2.235 | 20 ± 2.047 |
| Flakiness (↓) | 0.000 | 0.014 ± 0.035 | 0.007 ± 0.033 | 0.000 |
| Laufzeit (s) (↓) | 13.180 | 29.620 ± 10.517 | 20.880 ± 14.457 | 26.190 ± 15.980 |
| Judge: Correctness (↑) | 0.800 | 0.816 ± 0.098 | 0.782 ± 0.134 | 0.770 ± 0.128 |
| Judge: Appropriateness (↑) | 0.400 | 0.894 ± 0.037 | 0.758 ± 0.140 | 0.714 ± 0.160 |
| Judge: Hallucination (↓) | n/a | 0.084 ± 0.065 | 0.142 ± 0.162 | 0.146 ± 0.197 |
| Judge: Readability (↑) | 0.400 | 0.904 ± 0.040 | 0.854 ± 0.068 | 0.865 ± 0.066 |
| ISO: Correctness (↑) | 0.900 | 0.670 ± 0.102 | 0.666 ± 0.102 | 0.620 ± 0.115 |
| ISO: Completeness (↑) | 0.500 | 0.563 ± 0.193 | 0.543 ± 0.134 | 0.467 ± 0.193 |
| ISO: Appropriateness (↑) | 0.400 | 0.894 ± 0.037 | 0.758 ± 0.140 | 0.714 ± 0.160 |
| ISO: Functional Suitability (↑) | 0.600 | 0.709 ± 0.085 | 0.656 ± 0.094 | 0.600 ± 0.115 |

n/a = für diese Pipeline nicht anwendbar. ± x = Std über die Wiederholungen.

## Auffälligkeiten (über die Wiederholungen)

**Skript_L**
- Unterschiedliche Testanzahl pro Lauf: 6–15
- Hohe Varianz bei gen_time_s: 287.24 ± 130.5062
- Hohe Varianz bei flakiness: 0.014 ± 0.0349
- Hohe Varianz bei hallucination: 0.084 ± 0.065

**Skript_S**
- Instabil: in 1/50 Läufen alle Tests grün
- Hohe Varianz bei gen_time_s: 105.783 ± 73.6111
- Hohe Varianz bei flakiness: 0.007 ± 0.033
- Hohe Varianz bei duration_s: 20.879 ± 14.4569
- Hohe Varianz bei hallucination: 0.142 ± 0.1617

**Skript_H**
- Instabil: in 1/50 Läufen alle Tests grün
- Hohe Varianz bei ssr: 0.47 ± 0.1896
- Hohe Varianz bei exercised_coverage: 11.22 ± 4.5994
- Hohe Varianz bei duration_s: 26.191 ± 15.9799
- Hohe Varianz bei hallucination: 0.146 ± 0.1971
- Hohe Varianz bei iso_completeness: 0.467 ± 0.1934

## Detail je Pipeline

### Skript_C (crawler) · 1×
- Generierungszeit: 185.010 s · Modell: `(none)` · Provider: `crawler`
- Meta: `{'n_states': 9, 'n_edges': 8, 'n_scenarios': 30, 'element_coverage': 31, 'discovered_elements': 212, 'crawl_time_s': 184.79, 'locator_catalog': [{'label': 'Open Sidenav', 'role': 'button', 'locator': 'page.get_by_role("button", name="Open Sidenav").first', 'url': 'http://localhost:3000/?'}, {'label': 'Back to homepage', 'role': 'button', 'locator': 'page.get_by_role("button", name="Back to homepage").first', 'url': 'http://localhost:3000/?'}, {'label': 'Open search', 'role': 'button', 'locator': 'page.get_by_role("button", name="Open search").first', 'url': 'http://localhost:3000/?'}, {'label': 'input', 'role': 'textbox', 'locator': 'page.locator("#searchQuery > div > input")', 'url': 'http://localhost:3000/?'}, {'label': 'Close search', 'role': 'button', 'locator': 'page.get_by_role("button", name="Close search").first', 'url': 'http://localhost:3000/?'}, {'label': 'Show/hide account menu', 'role': 'button', 'locator': 'page.get_by_role("button", name="Show/hide account menu").first', 'url': 'http://localhost:3000/?'}, {'label': 'Show the shopping cart', 'role': 'button', 'locator': 'page.get_by_role("button", name="Show the shopping cart").first', 'url': 'http://localhost:3000/?'}, {'label': 'Language selection menu', 'role': 'button', 'locator': 'page.get_by_role("button", name="Language selection menu").first', 'url': 'http://localhost:3000/?'}, {'label': 'Click for more information about the product', 'role': 'button', 'locator': 'page.get_by_role("button", name="Click for more information about the product").first', 'url': 'http://localhost:3000/?'}, {'label': 'Add to Basket', 'role': 'button', 'locator': 'page.get_by_role("button", name="Add to Basket").first', 'url': 'http://localhost:3000/?'}, {'label': '16', 'role': 'combobox', 'locator': 'page.get_by_role("combobox", name="16").first', 'url': 'http://localhost:3000/?'}, {'label': 'Previous page', 'role': 'button', 'locator': 'page.get_by_role("button", name="Previous page").first', 'url': 'http://localhost:3000/?'}, {'label': 'Next page', 'role': 'button', 'locator': 'page.get_by_role("button", name="Next page").first', 'url': 'http://localhost:3000/?'}, {'label': 'div', 'role': 'generic', 'locator': 'page.locator("#cdk-overlay-0 > div:nth-of-type(1)")', 'url': 'http://localhost:3000/?'}, {'label': 'Welcome to OWASP Juice Shop!\n\nBeing a web application with a', 'role': 'dialog', 'locator': 'page.get_by_role("dialog", name="Welcome to OWASP Juice Shop!\\n\\nBeing a web application with a vast number of inte").first', 'url': 'http://localhost:3000/?'}, {'label': 'school\nHelp getting started', 'role': 'button', 'locator': 'page.get_by_role("button", name="school\\nHelp getting started").first', 'url': 'http://localhost:3000/?'}, {'label': 'Close Welcome Banner', 'role': 'button', 'locator': 'page.get_by_role("button", name="Close Welcome Banner").first', 'url': 'http://localhost:3000/?'}, {'label': 'div', 'role': 'generic', 'locator': 'page.locator("#cdk-overlay-0 > div:nth-of-type(2)")', 'url': 'http://localhost:3000/?'}, {'label': 'Force page reload', 'role': 'button', 'locator': 'page.get_by_role("button", name="Force page reload").first', 'url': 'http://localhost:3000/?'}, {'label': 'Apple Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Apple Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Apple Pomace', 'role': 'generic', 'locator': 'page.get_by_text("Apple Pomace", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Banana Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Banana Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Basil Smoothie', 'role': 'generic', 'locator': 'page.get_by_text("Basil Smoothie", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Berry Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Berry Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Best Juice Shop Salesman Artwork', 'role': 'generic', 'locator': 'page.get_by_text("Best Juice Shop Salesman Artwork", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Bragă (500ml)', 'role': 'generic', 'locator': 'page.get_by_text("Bragă (500ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Carrot Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Carrot Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Dragonfruit Juice (500ml)', 'role': 'generic', 'locator': 'page.get_by_text("Dragonfruit Juice (500ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Eggfruit Juice (500ml)', 'role': 'generic', 'locator': 'page.get_by_text("Eggfruit Juice (500ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Elderflower Cordial (500ml)', 'role': 'generic', 'locator': 'page.get_by_text("Elderflower Cordial (500ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Fruit Press', 'role': 'generic', 'locator': 'page.get_by_text("Fruit Press", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Grape Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Grape Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Green Smoothie', 'role': 'generic', 'locator': 'page.get_by_text("Green Smoothie", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Juice Shop "Permafrost" 2020 Edition', 'role': 'generic', 'locator': 'page.get_by_text("Juice Shop \\"Permafrost\\" 2020 Edition", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Lemon Juice (500ml)', 'role': 'generic', 'locator': 'page.get_by_text("Lemon Juice (500ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '16', 'role': 'generic', 'locator': 'page.get_by_text("16", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Dismiss', 'role': 'generic', 'locator': 'page.get_by_text("Dismiss", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Test', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Test")', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop\nContact\nfeedback\nCustomer Feedback\nauto_awe', 'role': 'generic', 'locator': 'page.locator("html > body > app-root > mat-sidenav-container > mat-sidenav")', 'url': 'http://localhost:3000/?'}, {'label': 'Go to contact us page', 'role': 'link', 'locator': 'page.get_by_role("link", name="Go to contact us page").first', 'url': 'http://localhost:3000/?'}, {'label': 'Go to AI chat page', 'role': 'link', 'locator': 'page.get_by_role("link", name="Go to AI chat page").first', 'url': 'http://localhost:3000/?'}, {'label': 'Go to about us page', 'role': 'link', 'locator': 'page.get_by_role("link", name="Go to about us page").first', 'url': 'http://localhost:3000/?'}, {'label': 'Go to photo wall', 'role': 'link', 'locator': 'page.get_by_role("link", name="Go to photo wall").first', 'url': 'http://localhost:3000/?'}, {'label': 'feedback\nCustomer Feedback', 'role': 'generic', 'locator': 'page.get_by_text("feedback\\nCustomer Feedback", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Customer Feedback', 'role': 'generic', 'locator': 'page.get_by_text("Customer Feedback", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'auto_awesome\nAI Chat\nIMPROVED', 'role': 'generic', 'locator': 'page.get_by_text("auto_awesome\\nAI Chat\\nIMPROVED", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'AI Chat', 'role': 'generic', 'locator': 'page.get_by_text("AI Chat", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'IMPROVED', 'role': 'generic', 'locator': 'page.get_by_text("IMPROVED", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'business_center\nAbout Us', 'role': 'generic', 'locator': 'page.get_by_text("business_center\\nAbout Us", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'About Us', 'role': 'generic', 'locator': 'page.get_by_text("About Us", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'camera\nPhoto Wall', 'role': 'generic', 'locator': 'page.get_by_text("camera\\nPhoto Wall", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Photo Wall', 'role': 'generic', 'locator': 'page.get_by_text("Photo Wall", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'school\nHelp getting started', 'role': 'generic', 'locator': 'page.get_by_text("school\\nHelp getting started", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Help getting started', 'role': 'generic', 'locator': 'page.get_by_text("Help getting started", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'GitHub', 'role': 'generic', 'locator': 'page.get_by_text("GitHub", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'exit_to_app\nLogin', 'role': 'menu', 'locator': 'page.get_by_role("menu", name="exit_to_app\\nLogin").first', 'url': 'http://localhost:3000/?'}, {'label': 'Go to login page', 'role': 'menuitem', 'locator': 'page.get_by_role("menuitem", name="Go to login page").first', 'url': 'http://localhost:3000/?'}, {'label': 'Login', 'role': 'generic', 'locator': 'page.get_by_text("Login", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'search\nSearch...\n Azərbaycanca\n Bahasa Indonesia\n Catalan\n Č', 'role': 'menu', 'locator': 'page.get_by_role("menu", name="search\\nSearch...\\n Azərbaycanca\\n Bahasa Indonesia\\n Catalan\\n Česky\\n Dansk\\n Deutsch").first', 'url': 'http://localhost:3000/?'}, {'label': 'input', 'role': 'textbox', 'locator': 'page.locator("#mat-input-0")', 'url': 'http://localhost:3000/?'}, {'label': 'Azərbaycanca', 'role': 'generic', 'locator': 'page.get_by_text("[object Object]", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Azərbaycanca', 'role': 'generic', 'locator': 'page.get_by_text("Azərbaycanca", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Bahasa Indonesia', 'role': 'generic', 'locator': 'page.get_by_text("Bahasa Indonesia", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Catalan', 'role': 'generic', 'locator': 'page.get_by_text("Catalan", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Česky', 'role': 'generic', 'locator': 'page.get_by_text("Česky", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Dansk', 'role': 'generic', 'locator': 'page.get_by_text("Dansk", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Deutsch', 'role': 'generic', 'locator': 'page.get_by_text("Deutsch", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Eesti', 'role': 'generic', 'locator': 'page.get_by_text("Eesti", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'English', 'role': 'generic', 'locator': 'page.get_by_text("English", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Español', 'role': 'generic', 'locator': 'page.get_by_text("Español", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Français', 'role': 'generic', 'locator': 'page.get_by_text("Français", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Gaeilge', 'role': 'generic', 'locator': 'page.get_by_text("Gaeilge", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Italiano', 'role': 'generic', 'locator': 'page.get_by_text("Italiano", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Język Polski', 'role': 'generic', 'locator': 'page.get_by_text("Język Polski", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Latvijas', 'role': 'generic', 'locator': 'page.get_by_text("Latvijas", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Magyar', 'role': 'generic', 'locator': 'page.get_by_text("Magyar", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Nederlands', 'role': 'generic', 'locator': 'page.get_by_text("Nederlands", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Norsk', 'role': 'generic', 'locator': 'page.get_by_text("Norsk", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Português', 'role': 'generic', 'locator': 'page.get_by_text("Português", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Português (Brasil)', 'role': 'generic', 'locator': 'page.get_by_text("Português (Brasil)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Pусский', 'role': 'generic', 'locator': 'page.get_by_text("Pусский", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Română', 'role': 'generic', 'locator': 'page.get_by_text("Română", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Schwizerdütsch', 'role': 'generic', 'locator': 'page.get_by_text("Schwizerdütsch", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Suomalainen', 'role': 'generic', 'locator': 'page.get_by_text("Suomalainen", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Svenska', 'role': 'generic', 'locator': 'page.get_by_text("Svenska", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Türkçe', 'role': 'generic', 'locator': 'page.get_by_text("Türkçe", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Ελληνικά', 'role': 'generic', 'locator': 'page.get_by_text("Ελληνικά", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'български (език)', 'role': 'generic', 'locator': 'page.get_by_text("български (език)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'український', 'role': 'generic', 'locator': 'page.get_by_text("український", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'ქართული', 'role': 'generic', 'locator': 'page.get_by_text("ქართული", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'עברית', 'role': 'generic', 'locator': 'page.get_by_text("עברית", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'انگلیسی', 'role': 'generic', 'locator': 'page.get_by_text("انگلیسی", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'عربي', 'role': 'generic', 'locator': 'page.get_by_text("عربي", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'हिंदी', 'role': 'generic', 'locator': 'page.get_by_text("हिंदी", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'বাংলা', 'role': 'generic', 'locator': 'page.get_by_text("বাংলা", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'සිංහල', 'role': 'generic', 'locator': 'page.get_by_text("සිංහල", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'ไทย', 'role': 'generic', 'locator': 'page.get_by_text("ไทย", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'မြန်မာ', 'role': 'generic', 'locator': 'page.get_by_text("မြန်မာ", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '한국어', 'role': 'generic', 'locator': 'page.get_by_text("한국어", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '中文', 'role': 'generic', 'locator': 'page.get_by_text("中文", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '日本語', 'role': 'generic', 'locator': 'page.get_by_text("日本語", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '繁體中文', 'role': 'generic', 'locator': 'page.get_by_text("繁體中文", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Apple Juice (1000ml)\nThe all-time classic.\n\n\n\n1.99¤\n\nReviews', 'role': 'dialog', 'locator': 'page.get_by_role("dialog", name="Apple Juice (1000ml)\\nThe all-time classic.\\n\\n\\n\\n1.99¤\\n\\nReviews\\n(5)\\nclose\\nClose").first', 'url': 'http://localhost:3000/?'}, {'label': 'Reviews\n(5)', 'role': 'button', 'locator': 'page.get_by_role("button", name="Reviews\\n(5)").first', 'url': 'http://localhost:3000/?'}, {'label': 'Close Dialog', 'role': 'button', 'locator': 'page.get_by_role("button", name="Close Dialog").first', 'url': 'http://localhost:3000/?'}, {'label': 'Reviews\n(5)', 'role': 'generic', 'locator': 'page.get_by_text("Reviews\\n(5)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Reviews', 'role': 'generic', 'locator': 'page.get_by_text("Reviews", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': '(5)', 'role': 'generic', 'locator': 'page.get_by_text("(5)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'X', 'role': 'button', 'locator': 'page.get_by_role("button", name="X").first', 'url': 'http://localhost:3000/?'}, {'label': 'Add to Basket', 'role': 'generic', 'locator': 'page.get_by_text("Add to Basket", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Melon Bike (Comeback-Product 2018 Edition)', 'role': 'generic', 'locator': 'page.get_by_text("Melon Bike (Comeback-Product 2018 Edition)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Melon Juice (1000ml)', 'role': 'generic', 'locator': 'page.get_by_text("Melon Juice (1000ml)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop "King of the Hill" Facemask', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop \\"King of the Hill\\" Facemask", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop CTF Girlie-Shirt', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop CTF Girlie-Shirt", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Card (non-foil)', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Card (non-foil)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Coaster (10pcs)', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Coaster (10pcs)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Holographic Sticker', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Holographic Sticker", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Hoodie', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Hoodie", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Iron-Ons (16pcs)', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Iron-Ons (16pcs)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop LEGO™ Tower', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop LEGO™ Tower", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Logo (3D-printed)', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Logo (3D-printed)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Magnets (16pcs)', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Magnets (16pcs)", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Mug', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Mug", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Sticker Page', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Sticker Page", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop Sticker Single', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop Sticker Single", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'OWASP Juice Shop T-Shirt', 'role': 'generic', 'locator': 'page.get_by_text("OWASP Juice Shop T-Shirt", exact=False).first', 'url': 'http://localhost:3000/?'}, {'label': 'Ask me anything', 'role': 'textbox', 'locator': 'page.get_by_placeholder("Ask me anything")', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'Send message', 'role': 'button', 'locator': 'page.get_by_role("button", name="Send message").first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'local_drink\nGet a suggestion', 'role': 'button', 'locator': 'page.get_by_role("button", name="local_drink\\nGet a suggestion").first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'help_outline\nGet help', 'role': 'button', 'locator': 'page.get_by_role("button", name="help_outline\\nGet help").first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'Get a suggestion', 'role': 'generic', 'locator': 'page.get_by_text("Get a suggestion", exact=False).first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'Get help', 'role': 'generic', 'locator': 'page.get_by_text("Get help", exact=False).first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'Account', 'role': 'generic', 'locator': 'page.get_by_text("Account", exact=False).first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'EN', 'role': 'generic', 'locator': 'page.get_by_text("EN", exact=False).first', 'url': 'http://localhost:3000/#/chatbot?'}, {'label': 'Text field for the login email', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Text field for the login email")', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Text field for the login password', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Text field for the login password")', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Button to display the password', 'role': 'button', 'locator': 'page.get_by_role("button", name="Button to display the password").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Forgot your password?', 'role': 'link', 'locator': 'page.get_by_role("link", name="Forgot your password?").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Login', 'role': 'button', 'locator': 'page.get_by_role("button", name="Login").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Checkbox to stay logged in or not logged in', 'role': 'generic', 'locator': 'page.get_by_text("on", exact=False).first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Login with Google', 'role': 'button', 'locator': 'page.get_by_role("button", name="Login with Google").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Not yet a customer?', 'role': 'link', 'locator': 'page.get_by_role("link", name="Not yet a customer?").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Button to hide the password', 'role': 'button', 'locator': 'page.get_by_role("button", name="Button to hide the password").first', 'url': 'http://localhost:3000/#/login?'}, {'label': 'Field with the name of the author', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field with the name of the author")', 'url': 'http://localhost:3000/#/contact?'}, {'label': 'Field for entering the comment or the feedback', 'role': 'textbox', 'locator': 'page.get_by_placeholder("What did you like or dislike?")', 'url': 'http://localhost:3000/#/contact?'}, {'label': '1', 'role': 'generic', 'locator': 'page.get_by_text("1", exact=False).first', 'url': 'http://localhost:3000/#/contact?'}, {'label': 'Field for the result of the CAPTCHA code', 'role': 'textbox', 'locator': 'page.get_by_placeholder("Please enter the result of the CAPTCHA.")', 'url': 'http://localhost:3000/#/contact?'}, {'label': 'Button to send the review', 'role': 'button', 'locator': 'page.get_by_role("button", name="Button to send the review").first', 'url': 'http://localhost:3000/#/contact?'}, {'label': '1★', 'role': 'generic', 'locator': 'page.get_by_text("1★", exact=False).first', 'url': 'http://localhost:3000/#/contact?'}, {'label': 'Link to the Terms of Use', 'role': 'link', 'locator': 'page.get_by_role("link", name="Link to the Terms of Use").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Next', 'role': 'button', 'locator': 'page.get_by_role("button", name="Next").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'BlueSky', 'role': 'button', 'locator': 'page.get_by_role("button", name="BlueSky").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Mastodon', 'role': 'button', 'locator': 'page.get_by_role("button", name="Mastodon").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Twitter', 'role': 'button', 'locator': 'page.get_by_role("button", name="Twitter").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Facebook', 'role': 'button', 'locator': 'page.get_by_role("button", name="Facebook").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Slack', 'role': 'button', 'locator': 'page.get_by_role("button", name="Slack").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Reddit', 'role': 'button', 'locator': 'page.get_by_role("button", name="Reddit").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Press Kit', 'role': 'button', 'locator': 'page.get_by_role("button", name="Press Kit").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'NFT', 'role': 'button', 'locator': 'page.get_by_role("button", name="NFT").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Previous', 'role': 'button', 'locator': 'page.get_by_role("button", name="Previous").first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'BlueSky', 'role': 'generic', 'locator': 'page.get_by_text("BlueSky", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Mastodon', 'role': 'generic', 'locator': 'page.get_by_text("Mastodon", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Twitter', 'role': 'generic', 'locator': 'page.get_by_text("Twitter", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Facebook', 'role': 'generic', 'locator': 'page.get_by_text("Facebook", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Slack', 'role': 'generic', 'locator': 'page.get_by_text("Slack", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Press Kit', 'role': 'generic', 'locator': 'page.get_by_text("Press Kit", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'NFT', 'role': 'generic', 'locator': 'page.get_by_text("NFT", exact=False).first', 'url': 'http://localhost:3000/#/about?'}, {'label': 'Tweet', 'role': 'button', 'locator': 'page.get_by_role("button", name="Tweet").first', 'url': 'http://localhost:3000/#/photo-wall?'}, {'label': 'Email address field', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Email address field")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Field for the password', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field for the password")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Field to confirm the password', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field to confirm the password")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'button', 'role': 'switch', 'locator': 'page.locator("#mat-mdc-slide-toggle-0-button")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Selection list for the security question', 'role': 'combobox', 'locator': 'page.get_by_role("combobox", name="Selection list for the security question").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Field for the answer to the security question', 'role': 'textbox', 'locator': 'page.get_by_placeholder("Answer to your security question")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Button to complete the registration', 'role': 'button', 'locator': 'page.get_by_role("button", name="Button to complete the registration").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Already a customer?', 'role': 'link', 'locator': 'page.get_by_role("link", name="Already a customer?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Security Question', 'role': 'generic', 'locator': 'page.get_by_text("Security Question", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'mat-progress-bar', 'role': 'progressbar', 'locator': 'page.locator("#registration-form > app-password-strength > mat-progress-bar")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Selection list for the security question', 'role': 'listbox', 'locator': 'page.get_by_role("listbox", name="Selection list for the security question").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your eldest siblings middle name?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Your eldest siblings middle name?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Mother's maiden name?", 'role': 'option', 'locator': 'page.get_by_role("option", name="Mother\'s maiden name?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Mother's birth date? (MM/DD/YY)", 'role': 'option', 'locator': 'page.get_by_role("option", name="Mother\'s birth date? (MM/DD/YY)").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Father's birth date? (MM/DD/YY)", 'role': 'option', 'locator': 'page.get_by_role("option", name="Father\'s birth date? (MM/DD/YY)").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Maternal grandmother's first name?", 'role': 'option', 'locator': 'page.get_by_role("option", name="Maternal grandmother\'s first name?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Paternal grandmother's first name?", 'role': 'option', 'locator': 'page.get_by_role("option", name="Paternal grandmother\'s first name?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Name of your favorite pet?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Name of your favorite pet?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Last name of dentist when you were a teenager? (Do not inclu', 'role': 'option', 'locator': 'page.get_by_role("option", name="Last name of dentist when you were a teenager? (Do not include \'Dr.\')").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your ZIP/postal code when you were a teenager?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Your ZIP/postal code when you were a teenager?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Company you first work for as an adult?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Company you first work for as an adult?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your favorite book?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Your favorite book?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your favorite movie?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Your favorite movie?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Number of one of your customer or ID cards?', 'role': 'option', 'locator': 'page.get_by_role("option", name="Number of one of your customer or ID cards?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': "What's your favorite place to go hiking?", 'role': 'option', 'locator': 'page.get_by_role("option", name="What\'s your favorite place to go hiking?").first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your eldest siblings middle name?', 'role': 'generic', 'locator': 'page.get_by_text("Your eldest siblings middle name?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Mother's maiden name?", 'role': 'generic', 'locator': 'page.get_by_text("Mother\'s maiden name?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Mother's birth date? (MM/DD/YY)", 'role': 'generic', 'locator': 'page.get_by_text("Mother\'s birth date? (MM/DD/YY)", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Father's birth date? (MM/DD/YY)", 'role': 'generic', 'locator': 'page.get_by_text("Father\'s birth date? (MM/DD/YY)", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Maternal grandmother's first name?", 'role': 'generic', 'locator': 'page.get_by_text("Maternal grandmother\'s first name?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "Paternal grandmother's first name?", 'role': 'generic', 'locator': 'page.get_by_text("Paternal grandmother\'s first name?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Name of your favorite pet?', 'role': 'generic', 'locator': 'page.get_by_text("Name of your favorite pet?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Last name of dentist when you were a teenager? (Do not inclu', 'role': 'generic', 'locator': 'page.locator("#mat-option-42 > span")', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your ZIP/postal code when you were a teenager?', 'role': 'generic', 'locator': 'page.get_by_text("Your ZIP/postal code when you were a teenager?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Company you first work for as an adult?', 'role': 'generic', 'locator': 'page.get_by_text("Company you first work for as an adult?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your favorite book?', 'role': 'generic', 'locator': 'page.get_by_text("Your favorite book?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Your favorite movie?', 'role': 'generic', 'locator': 'page.get_by_text("Your favorite movie?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Number of one of your customer or ID cards?', 'role': 'generic', 'locator': 'page.get_by_text("Number of one of your customer or ID cards?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': "What's your favorite place to go hiking?", 'role': 'generic', 'locator': 'page.get_by_text("What\'s your favorite place to go hiking?", exact=False).first', 'url': 'http://localhost:3000/#/register?'}, {'label': 'Email address field', 'role': 'textbox', 'locator': 'page.get_by_placeholder("Enter your email")', 'url': 'http://localhost:3000/#/forgot-password?'}, {'label': 'Field for the answer to the security question', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field for the answer to the security question")', 'url': 'http://localhost:3000/#/forgot-password?'}, {'label': 'Field for New Password', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field for New Password")', 'url': 'http://localhost:3000/#/forgot-password?'}, {'label': 'Field to confirm the new password', 'role': 'textbox', 'locator': 'page.get_by_role("textbox", name="Field to confirm the new password")', 'url': 'http://localhost:3000/#/forgot-password?'}, {'label': 'Button to confirm the changes', 'role': 'button', 'locator': 'page.get_by_role("button", name="Button to confirm the changes").first', 'url': 'http://localhost:3000/#/forgot-password?'}], 'routes': ['http://localhost:3000/#/about?', 'http://localhost:3000/#/chatbot?', 'http://localhost:3000/#/contact?', 'http://localhost:3000/#/forgot-password?', 'http://localhost:3000/#/login?', 'http://localhost:3000/#/photo-wall?', 'http://localhost:3000/#/register?', 'http://localhost:3000/?', 'http://localhost:3000/ftp/legal.md?']}`
- Judge-Begründungen:
  - **hallucination**: n/a (für diese Pipeline nicht anwendbar)
  - **readability**: The test names (e.g., 'test_scenario_1') are generic and fail to convey their specific purpose, relying entirely on docstrings to describe actions. The structure is well-organized and consistent, properly utilizing Playwright sync API and aligning with the discovered routes. However, the comments are highly redundant; the identical 'Robust smoke assertion' comment is repeated in every test, violating the guideline to avoid redundancy. Furthermore, the assertions are weak smoke checks rather than
  - **correctness**: The test suite is internally coherent and logically consistent. The actions in the Input, such as navigating to valid routes like /#/chatbot, /#/login, and /#/contact, directly correspond to the interactions in the Actual Output. The assertions are robust smoke checks that verify the body is attached to the DOM, avoiding false failures from overlays. While the assertions are generic and do not validate specific outcomes of the actions (e.g., verifying a successful login or message send), they ar
  - **appropriateness**: The test suite covers plausible user-facing flows across the discovered routes (e.g., login, register, chatbot, contact), but falls short on locator robustness and assertion quality. While many tests correctly use web-first locators like get_by_role and get_by_placeholder, several scenarios (1, 16, 17) rely on brittle CSS selectors (e.g., '#mat-input-0' and 'app-chat-welcome-screen > div > div:nth-of-type(2)...'). Furthermore, every test concludes with a weak assertion checking only if the 'body

<details><summary>Skript_C — Code</summary>

```python
"""Skript_C — autonomously generated Web-UI test suite (traditional crawler).

Target : OWASP Juice Shop (http://localhost:3000)
States : 9   Transitions: 8   Crawl time: 184.79s
Generated by the crawler pipeline; no user story was consulted.
"""

import pytest
from playwright.sync_api import Page, expect


def test_scenario_1(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Language selection menu' -> fill '' = 'MacBook' + Enter"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Language selection menu").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Language selection menu").first.dispatch_event("click")
    page.wait_for_load_state()
    page.locator("#mat-input-0").fill("MacBook")
    page.locator("#mat-input-0").press("Enter")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_2(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Open Sidenav'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Open Sidenav").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Open Sidenav").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_3(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Back to homepage'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Back to homepage").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Back to homepage").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_4(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Show/hide account menu'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Show/hide account menu").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Show/hide account menu").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_5(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Show the shopping cart'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Show the shopping cart").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Show the shopping cart").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_6(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Click for more information about the product'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Click for more information about the product").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Click for more information about the product").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_7(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Add to Basket'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Add to Basket").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Add to Basket").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_8(page: Page) -> None:
    """goto http://localhost:3000/#/ -> click 'Next page'"""
    page.goto("http://localhost:3000/#/")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Next page").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Next page").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_9(page: Page) -> None:
    """goto http://localhost:3000/#/chatbot -> fill 'Ask me anything' = 'Test'"""
    page.goto("http://localhost:3000/#/chatbot")
    page.wait_for_load_state()
    page.get_by_placeholder("Ask me anything").fill("Test")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_10(page: Page) -> None:
    """goto http://localhost:3000/#/login -> fill 'Text field for the login email' = 'tester@example.com'"""
    page.goto("http://localhost:3000/#/login")
    page.wait_for_load_state()
    page.get_by_role("textbox", name="Text field for the login email").fill("tester@example.com")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_11(page: Page) -> None:
    """goto http://localhost:3000/#/login -> fill 'Text field for the login password' = 'Passw0rd!'"""
    page.goto("http://localhost:3000/#/login")
    page.wait_for_load_state()
    page.get_by_role("textbox", name="Text field for the login password").fill("Passw0rd!")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_12(page: Page) -> None:
    """goto http://localhost:3000/#/contact -> fill 'Field for entering the comment or the feedback' = 'Test'"""
    page.goto("http://localhost:3000/#/contact")
    page.wait_for_load_state()
    page.get_by_placeholder("What did you like or dislike?").fill("Test")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_13(page: Page) -> None:
    """goto http://localhost:3000/#/contact -> fill 'Field for the result of the CAPTCHA code' = 'Test'"""
    page.goto("http://localhost:3000/#/contact")
    page.wait_for_load_state()
    page.get_by_placeholder("Please enter the result of the CAPTCHA.").fill("Test")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_14(page: Page) -> None:
    """goto http://localhost:3000/#/login -> click 'Button to display the password'"""
    page.goto("http://localhost:3000/#/login")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Button to display the password").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Button to display the password").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_15(page: Page) -> None:
    """goto http://localhost:3000/#/chatbot -> click 'Send message'"""
    page.goto("http://localhost:3000/#/chatbot")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Send message").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Send message").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_16(page: Page) -> None:
    """goto http://localhost:3000/#/chatbot -> click 'local_drink\nGet a suggestion'"""
    page.goto("http://localhost:3000/#/chatbot")
    page.wait_for_load_state()
    try:
        page.locator("app-chat-welcome-screen > div > div:nth-of-type(2) > div > button:nth-of-type(1)").click(timeout=2500)
    except Exception:
        page.locator("app-chat-welcome-screen > div > div:nth-of-type(2) > div > button:nth-of-type(1)").dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_17(page: Page) -> None:
    """goto http://localhost:3000/#/chatbot -> click 'help_outline\nGet help'"""
    page.goto("http://localhost:3000/#/chatbot")
    page.wait_for_load_state()
    try:
        page.locator("app-chat-welcome-screen > div > div:nth-of-type(2) > div > button:nth-of-type(2)").click(timeout=2500)
    except Exception:
        page.locator("app-chat-welcome-screen > div > div:nth-of-type(2) > div > button:nth-of-type(2)").dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_18(page: Page) -> None:
    """goto http://localhost:3000/#/contact -> click 'Button to send the review'"""
    page.goto("http://localhost:3000/#/contact")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Button to send the review").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Button to send the review").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_19(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Next'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Next").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Next").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_20(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'BlueSky'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="BlueSky").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="BlueSky").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_21(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Mastodon'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Mastodon").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Mastodon").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_22(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Twitter'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Twitter").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Twitter").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_23(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Facebook'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Facebook").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Facebook").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_24(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Slack'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Slack").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Slack").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_25(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'Press Kit'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="Press Kit").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="Press Kit").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_26(page: Page) -> None:
    """goto http://localhost:3000/#/about -> click 'NFT'"""
    page.goto("http://localhost:3000/#/about")
    page.wait_for_load_state()
    try:
        page.get_by_role("button", name="NFT").first.click(timeout=2500)
    except Exception:
        page.get_by_role("button", name="NFT").first.dispatch_event("click")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_27(page: Page) -> None:
    """goto http://localhost:3000/#/register -> fill 'Email address field' = 'Test'"""
    page.goto("http://localhost:3000/#/register")
    page.wait_for_load_state()
    page.get_by_role("textbox", name="Email address field").fill("Test")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_28(page: Page) -> None:
    """goto http://localhost:3000/#/forgot-password -> fill 'Email address field' = 'tester@example.com'"""
    page.goto("http://localhost:3000/#/forgot-password")
    page.wait_for_load_state()
    page.get_by_placeholder("Enter your email").fill("tester@example.com")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_29(page: Page) -> None:
    """goto http://localhost:3000/#/register -> fill 'Field for the password' = 'Passw0rd!'"""
    page.goto("http://localhost:3000/#/register")
    page.wait_for_load_state()
    page.get_by_role("textbox", name="Field for the password").fill("Passw0rd!")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_30(page: Page) -> None:
    """goto http://localhost:3000/#/register -> fill 'Field to confirm the password' = 'Passw0rd!'"""
    page.goto("http://localhost:3000/#/register")
    page.wait_for_load_state()
    page.get_by_role("textbox", name="Field to confirm the password").fill("Passw0rd!")
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()
```
</details>

### Skript_L (llm_agent) · 50×
- Generierungszeit: 57.840 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_contact_page_feedback_form[chromium]: - button "Force page reload"
- Meta: `{'agent_steps': 19, 'pages_observed': 6, 'user_story_used': False, 'browser_backend': 'inprocess', 'grounded_agent': False, 'postprocess_fixes': [], 'runtime_repair_rounds': 2, 'ssr_before_repair': 0.6667, 'ssr_after_repair': 0.8889, 'runtime_repair_time_s': 62.98}`
- Judge-Begründungen:
  - **correctness**: The interactions in the test suite are internally coherent and logically consistent. The assertions in the Actual Output directly follow from the actions performed in the Input, such as verifying the visibility of 'Apple Juice (1000ml)' and 'Banana Juice (1000ml)' after navigating to the homepage. There are no contradictory or meaningless checks between the Input and Actual Output. However, some assertions rely on elements not explicitly listed in the known application surface, such as 'Open Sid
  - **appropriateness**: The test suite exercises plausible user-facing flows across the discovered application surface, including homepage product visibility, sidenav navigation, search, product details, contact feedback, chatbot, login, and registration. It adheres strongly to web-first locators, predominantly using `get_by_role` and `get_by_text` with accessible names matching the input labels (e.g., 'Ask me anything', 'Add to Basket', 'Field for the answer to the security question'). It also correctly utilizes Playw
  - **readability**: The test names are highly descriptive and clearly convey their purpose, such as 'test_homepage_loads_and_shows_products' and 'test_contact_page_feedback_form'. The structure is well-organized, with each test logically mapping to a specific route or UI element from the input, like the chatbot, login, and registration pages. Comments are absent, which aligns well with the requirement to avoid redundancy. There is no dead code, and all elements interacted with are relevant to the discovered applica
  - **hallucination**: The test suite demonstrates strong alignment with the Known Application Surface. It accurately references existing routes like `/#/contact`, `/#/chatbot`, `/#/login`, and `/#/register`, and correctly uses observed UI elements such as 'Apple Juice (1000ml)', 'Add to Basket', 'Open search', and 'Field for the answer to the security question'. Unobserved references like 'Open Sidenav', 'Send message', 'Show/hide account menu', and 'Text field for the login email' are highly plausible for a standard
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_L — Code</summary>

```python
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:3000"


def test_homepage_loads_and_shows_products(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("body")).to_be_attached()
    expect(page.get_by_role("button", name="Open Sidenav")).to_be_visible()
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.get_by_text("Banana Juice (1000ml)").first).to_be_visible()
    expect(page.get_by_role("button", name="Add to Basket").first).to_be_visible()


def test_sidenav_navigation_links(page: Page):
    page.goto(BASE_URL)
    page.get_by_role("button", name="Open Sidenav").click()
    expect(page.get_by_role("link", name="Go to contact us page")).to_be_visible()
    expect(page.get_by_role("link", name="Go to AI chat page")).to_be_visible()
    expect(page.get_by_role("link", name="Go to about us page")).to_be_visible()
    expect(page.get_by_role("link", name="Go to photo wall")).to_be_visible()
    expect(page.get_by_role("link", name="Go to OWASP Juice Shop GitHub page")).to_be_visible()


def test_search_flow(page: Page):
    page.goto(BASE_URL)
    page.get_by_role("button", name="Open search").click()
    page.get_by_role("textbox").fill("Apple")
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.get_by_text("Apple Pomace").first).to_be_visible()
    page.get_by_role("button", name="Close search").click()


def test_product_detail_view(page: Page):
    page.goto(BASE_URL)
    page.get_by_role("button", name="Click for more information about the product").first.click()
    expect(page.get_by_role("button", name="Add to Basket").first).to_be_visible()
    expect(page.get_by_role("button", name="Back to homepage")).to_be_visible()


def test_contact_page_feedback_form(page: Page):
    page.goto(f"{BASE_URL}/#/contact")
    expect(page.get_by_text("Customer Feedback").first).to_be_visible()
    page.get_by_role("textbox", name="Field with the name of the author").fill("Test User")
    page.get_by_role("textbox", name="Field for entering the comment or the feedback").fill("Great shop!")
    page.get_by_role("textbox", name="Field for the result of the CAPTCHA code").fill("1")
    expect(page.get_by_role("button", name="Button to send the review").first).to_be_visible()


def test_chatbot_flow(page: Page):
    page.goto(f"{BASE_URL}/#/chatbot")
    expect(page.get_by_role("textbox", name="Ask me anything").first).to_be_visible()
    expect(page.get_by_role("button", name="Send message").first).to_be_visible()
    expect(page.get_by_text("Get a suggestion").first).to_be_visible()
    expect(page.get_by_text("Get help").first).to_be_visible()
    page.get_by_role("textbox", name="Ask me anything").first.fill("Hello, what can you do?")
    page.get_by_role("button", name="Send message").first.click()
    expect(page.get_by_text("Hello, what can you do?").first).to_be_attached()


def test_login_with_test_account(page: Page):
    page.goto(f"{BASE_URL}/#/login")
    expect(page.get_by_role("textbox", name="Text field for the login email")).to_be_visible()
    page.get_by_role("textbox", name="Text field for the login email").fill("test@juice.sh")
    page.get_by_role("textbox", name="Text field for the login password").fill("Test1234!")
    page.get_by_role("button", name="Login").first.click()
    expect(page.get_by_role("button", name="Show/hide account menu")).to_be_visible()


def test_register_page_elements(page: Page):
    page.goto(f"{BASE_URL}/#/register")
    expect(page.get_by_role("textbox", name="Email address field")).to_be_visible()
    expect(page.get_by_role("textbox", name="Field for the password")).to_be_visible()
    expect(page.get_by_role("textbox", name="Field to confirm the password")).to_be_visible()
    expect(page.get_by_role("combobox", name="Selection list for the security question")).to_be_visible()
    expect(page.get_by_role("textbox", name="Field for the answer to the security question")).to_be_visible()
    expect(page.get_by_role("button", name="Button to complete the registration")).to_be_visible()
    expect(page.get_by_role("link", name="Already a customer?")).to_be_visible()


def test_account_menu_login_link(page: Page):
    page.goto(BASE_URL)
    page.get_by_role("button", name="Show/hide account menu").click()
    expect(page.get_by_role("menuitem", name="Go to login page")).to_be_visible()
    page.get_by_role("menuitem", name="Go to login page").click()
    expect(page.get_by_role("textbox", name="Text field for the login email")).to_be_visible()
```
</details>

### Skript_S (llm_agent_story) · 50×
- Generierungszeit: 42.090 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_us5_login_with_existing_account[chromium]:   - waiting for get_by_role("button", name="Login")
- Meta: `{'agent_steps': 14, 'pages_observed': 3, 'user_story_used': True, 'browser_backend': 'inprocess', 'grounded_agent': False, 'postprocess_fixes': ['to_have_url(regex-string) -> re.compile(...)', 'import re ergänzt'], 'runtime_repair_rounds': 1, 'ssr_before_repair': 0.8333, 'ssr_after_repair': 0.8333, 'runtime_repair_time_s': 31.79}`
- Judge-Begründungen:
  - **correctness**: The Playwright tests accurately follow the sequence of steps described in the user stories and cover most acceptance criteria. US-1, US-2, US-6, and US-7 are well tested, including verifying search results, dialog visibility, product details, and cart counter updates. However, US-5 falls short in asserting the account confirmation in the header, as it only checks for the visibility of the account menu button rather than verifying an account name or specific logged-in state. US-3 correctly checks
  - **readability**: The test names are highly descriptive and map directly to the user stories (e.g., test_us1_product_search). The structure is well-organized, cleanly separating each user story into its own test function. Comments are used effectively to delineate logical steps within the tests without cluttering the code. The tests accurately utilize the provided application surface, such as 'Apple Juice (1000ml)', 'Add to Basket', and 'Close Dialog'. A minor shortcoming is the presence of unused module-level va
  - **hallucination**: The test script references standard UI elements and routes that align well with the Known Application Surface. Elements like 'Open search', 'Close search', 'Apple Juice (1000ml)', 'Add to Basket', and 'Close Dialog' are explicitly found in the provided UI elements list. Routes such as '#/login' and '#/register' match the discovered routes. The script plausibly interacts with the application for the user stories, including searching, opening dialogs, and adding to the cart. A minor deduction is m
  - **appropriateness**: The test functions accurately target the scenarios described in the input without redundant steps. It correctly utilizes user-facing locators like `get_by_role` and `get_by_text` for elements such as 'Open search', 'Add to Basket', and 'Apple Juice (1000ml)'. Web-first assertions are properly used to validate expected outcomes, such as checking dialog visibility and cart counter text. However, some assertions fall short of web-first best practices by using `page.locator("body")` to check for tex
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_S — Code</summary>

```python
from playwright.sync_api import Page, expect
import re


BASE_URL = "http://localhost:3000"

TEST_EMAIL = "test@juice.sh"
TEST_PASSWORD = "Test1234!"


def test_us1_product_search(page: Page):
    """US-1: Search for a product via the header search icon."""
    page.goto(BASE_URL)

    # Open search field via header icon
    page.get_by_role("button", name="Open search").click()
    expect(page.get_by_role("button", name="Close search")).to_be_visible()

    # Search for Apple
    page.get_by_role("textbox").fill("Apple")
    page.keyboard.press("Enter")

    # Result list contains product tiles/cards
    apple_juice = page.get_by_text("Apple Juice (1000ml)")
    apple_pomace = page.get_by_text("Apple Pomace")
    expect(apple_juice.or_(apple_pomace).first).to_be_visible()


def test_us2_open_product_details(page: Page):
    """US-2: Open and close a product detail dialog."""
    page.goto(BASE_URL)

    # Open detail dialog by clicking a product card/info button
    page.get_by_text("Apple Juice (1000ml)").click()
    dialog = page.get_by_role("dialog")
    expect(dialog.first).to_be_visible()

    # Dialog shows product name and price
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.locator("body")).to_contain_text("1.99")

    # Close dialog
    page.get_by_role("button", name="Close Dialog").click()
    expect(dialog.first).to_be_attached()


def test_us3_register_account_form(page: Page):
    """US-3: Registration page reachable with required fields."""
    page.goto(BASE_URL)

    # Open account menu and navigate to register
    page.get_by_role("button", name="Show/hide account menu").click()
    page.get_by_role("menuitem", name="Go to login page").click()
    expect(page).to_have_url(re.compile(r".*#/login"))

    page.get_by_role("link", name="Not yet a customer?").click()
    expect(page).to_have_url(re.compile(r".*#/register"))

    # Required fields present
    expect(page.get_by_role("textbox", name="Email address field")).to_be_visible()
    expect(page.get_by_role("textbox", name="Field for the password")).to_be_visible()
    expect(page.get_by_role("textbox", name="Field to confirm the password")).to_be_visible()

    # Security question must be selectable
    expect(page.get_by_role("combobox", name="Selection list for the security question")).to_be_visible()


def test_us5_login_with_existing_account(page: Page):
    """US-5: Log in with existing customer account."""
    page.goto(BASE_URL)

    # Open account menu and navigate to login
    page.get_by_role("button", name="Show/hide account menu").click()
    page.get_by_role("menuitem", name="Go to login page").click()
    expect(page).to_have_url(re.compile(r".*#/login"))

    # Login form fields present
    expect(page.get_by_role("textbox", name="Text field for the login email")).to_be_visible()
    expect(page.get_by_role("textbox", name="Text field for the login password")).to_be_visible()

    # Fill credentials and submit
    page.get_by_role("textbox", name="Text field for the login email").fill(TEST_EMAIL)
    page.get_by_role("textbox", name="Text field for the login password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Login").click()

    # Redirected back to shop view
    expect(page).to_have_url(re.compile(r".*#/$"))

    # Header shows account confirmation (account menu button / cart area reachable)
    expect(page.get_by_role("button", name="Show/hide account menu")).to_be_visible()
    expect(page.get_by_role("button", name="Show the shopping cart")).to_be_visible()


def test_us6_add_product_to_basket(page: Page):
    """US-6: Add a product to the shopping cart from a product card."""
    page.goto(BASE_URL)

    # Add first product to basket
    add_buttons = page.get_by_role("button", name="Add to Basket")
    add_buttons.first.click()

    # Confirmation toast/message appears
    expect(page.locator("body")).to_contain_text("Placed")

    # Cart icon shows at least 1 item
    cart_button = page.get_by_role("button", name="Show the shopping cart")
    expect(cart_button).to_contain_text("1")


def test_us7_full_search_to_cart_flow(page: Page):
    """US-7: Search, open details, and add product to cart end-to-end."""
    page.goto(BASE_URL)

    # Search for Apple
    page.get_by_role("button", name="Open search").click()
    page.get_by_role("textbox").fill("Apple")
    page.keyboard.press("Enter")

    # At least one Apple product card visible
    apple_product = page.get_by_text("Apple Juice (1000ml)")
    expect(apple_product.first).to_be_visible()

    # Open detail dialog
    apple_product.first.click()
    dialog = page.get_by_role("dialog")
    expect(dialog.first).to_be_visible()

    # Dialog shows name and price
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.locator("body")).to_contain_text("1.99")

    # Add to basket from detail dialog
    page.get_by_role("button", name="Add to Basket").first.click()
    expect(page.locator("body")).to_contain_text("Placed")

    # Cart counter increased to at least 1
    cart_button = page.get_by_role("button", name="Show the shopping cart")
    expect(cart_button).to_contain_text("1")
```
</details>

### Skript_H (hybrid) · 50×
- Generierungszeit: 221.120 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_us2_open_product_details[chromium]: - button "Force page reload"
- Meta: `{'agent_steps': 10, 'pages_observed': 1, 'user_story_used': True, 'browser_backend': 'inprocess', 'grounded_agent': True, 'postprocess_fixes': [], 'grounded_routes': 9, 'grounded_locators': 212, 'refined_from': 'crawler', 'exploration_time_s': 184.79, 'input_element_coverage': 31, 'domain_context_used': False, 'runtime_repair_rounds': 1, 'ssr_before_repair': 0.3333, 'ssr_after_repair': 0.3333, 'runtime_repair_time_s': 48.97}`
- Judge-Begründungen:
  - **hallucination**: All referenced UI elements, routes, and selectors plausibly exist based on the Input. The script correctly uses the base URL 'http://localhost:3000' and interacts with elements explicitly named in the Known Application Surface, such as 'Apple Juice (1000ml)', 'Apple Pomace', 'Close Dialog', and 'Add to Basket'. Standard components for this application type, like 'Open search', 'Show/hide account menu', and 'Show the shopping cart', are used appropriately without being penalized for not being exp
  - **readability**: The actual output demonstrates strong readability and maintainability with descriptive test names (e.g., test_us1_product_search) and clear docstrings mapping to user stories. The structure is clean, and there is no dead code or redundant commentary. However, some assertions are weak or potentially incorrect: US-2 checks page.locator('body').to_be_attached() instead of verifying product price, and US-3 uses 'Not yet a customer?' instead of the crawler-discovered 'Already a customer?' label, slig
  - **appropriateness**: The test suite accurately targets the scenarios described in the input, covering all user stories from US-1 to US-7. It effectively uses user-facing Playwright locators like `get_by_role` and `get_by_text`, aligning well with the known application surface (e.g., 'Apple Juice (1000ml)', 'Add to Basket'). The tests rely on web-first assertions, avoiding manual waits. However, there are minor shortcomings: US-2 uses a non-specific `expect(page.locator("body")).to_be_attached()` instead of verifying
  - **correctness**: The Playwright tests correctly follow the user flows for most stories, but miss critical assertions specified in the acceptance criteria. US-1, US-6, and US-7 are well tested, properly validating search results, basket confirmation messages, and the shopping cart counter. However, US-2 fails to assert that the price is visible in the detail dialog, only checking the product name. US-3 verifies the presence of mandatory fields and the security question, but misses asserting the presence of the ac
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_H — Code</summary>

```python
from playwright.sync_api import Page, expect


def test_us1_product_search(page: Page):
    """US-1: Search for a product via the header search icon."""
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Open search").click()
    expect(page.get_by_role("textbox")).to_be_visible()
    page.get_by_role("textbox").fill("Apple")
    page.keyboard.press("Enter")
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.get_by_text("Apple Pomace").first).to_be_visible()


def test_us2_open_product_details(page: Page):
    """US-2: Click a product tile to open its detail dialog."""
    page.goto("http://localhost:3000")
    page.get_by_text("Apple Juice (1000ml)").first.click()
    dialog = page.get_by_role("dialog", name="Apple Juice (1000ml)")
    expect(dialog).to_be_visible()
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    expect(page.locator("body")).to_be_attached()
    page.get_by_role("button", name="Close Dialog").click()
    expect(dialog).not_to_be_visible()


def test_us3_register_account_form_elements(page: Page):
    """US-3: Registration page is reachable and contains required fields."""
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Show/hide account menu").click()
    page.get_by_role("menuitem", name="Go to login page").click()
    expect(page.locator("body")).to_be_attached()
    page.get_by_role("button", name="Show/hide account menu").click()
    page.get_by_role("menuitem", name="Not yet a customer?").click()
    expect(page.get_by_role("textbox", name="Email address")).to_be_visible()
    expect(page.get_by_role("textbox", name="Password")).to_be_visible()
    expect(page.get_by_role("textbox", name="Repeat Password")).to_be_visible()
    expect(page.get_by_role("combobox", name="Security Question")).to_be_visible()


def test_us5_login_with_test_account(page: Page):
    """US-5: Log in with the provided test account."""
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Show/hide account menu").click()
    page.get_by_role("menuitem", name="Go to login page").click()
    expect(page.get_by_role("textbox", name="Email address")).to_be_visible()
    expect(page.get_by_role("textbox", name="Password")).to_be_visible()
    page.get_by_role("textbox", name="Email address").fill("test@juice.sh")
    page.get_by_role("textbox", name="Password").fill("Test1234!")
    page.get_by_role("button", name="Log in").click()
    expect(page.get_by_role("button", name="Show/hide account menu")).to_be_visible()
    page.get_by_role("button", name="Show/hide account menu").click()
    expect(page.get_by_text("test@juice.sh").first).to_be_visible()


def test_us6_add_product_to_basket(page: Page):
    """US-6: Add a product to the basket from a product card."""
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Add to Basket").first.click()
    expect(page.get_by_text("Placed Apple Juice (1000ml) into basket.").first).to_be_visible()
    expect(page.get_by_role("button", name="Show the shopping cart")).to_contain_text("1")


def test_us7_full_search_to_basket_flow(page: Page):
    """US-7: Search, open details, and add product to basket end-to-end."""
    page.goto("http://localhost:3000")
    page.get_by_role("button", name="Open search").click()
    page.get_by_role("textbox").fill("Apple")
    page.keyboard.press("Enter")
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    page.get_by_text("Apple Juice (1000ml)").first.click()
    dialog = page.get_by_role("dialog", name="Apple Juice (1000ml)")
    expect(dialog).to_be_visible()
    expect(page.get_by_text("Apple Juice (1000ml)").first).to_be_visible()
    page.get_by_role("button", name="Add to Basket").first.click()
    expect(page.get_by_text("Placed Apple Juice (1000ml) into basket.").first).to_be_visible()
    expect(page.get_by_role("button", name="Show the shopping cart")).to_contain_text("1")
    page.get_by_role("button", name="Close Dialog").click()
    expect(dialog).not_to_be_visible()
```
</details>
