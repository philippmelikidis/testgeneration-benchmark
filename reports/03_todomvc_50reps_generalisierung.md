> **TodoMVC (50 Reps) — interner Generalisierungstest**
>
> Teil des Ergebnis-Verlaufs. Roh-Record: `20260710-082622_todomvc_515845`.

# Ergebnisbericht — TodoMVC (React)

- Experiment: `20260710-082622_todomvc_515845`
- Provider / Modell: `ollama` / `kimi-k2.7-code:cloud`
- Zeitpunkt: 2026-07-10T08:26:22+00:00
- Notes: coverage_denominator=4 (crawler_affordances) repetitions=50 judge_model=glm-5.2:cloud judge_in_family=False stories=['US-1', 'US-2', 'US-3', 'US-4', 'US-5', 'US-6', 'US-7']

## Vergleichstabelle — Metrik × Pipeline

| Metrik | Skript_C | Skript_L | Skript_S | Skript_H |
|---|---|---|---|---|
| Gen-Zeit (s) (↓) | 3.840 | 27.770 ± 27.338 | 47.250 ± 36.034 | 21.220 ± 61.967 |
| Ausführbar (↑) | ja | ja | ja | ja |
| Alle Tests grün (↑) | ja | ja | nein | nein |
| # Tests | 4 | 4 ± 1.460 | 7 | 7 |
| SSR (Pass-Rate) (↑) | 1.000 | 0.937 ± 0.130 | 0.609 ± 0.135 | 0.600 ± 0.138 |
| Element-Coverage (genutzt) (↑) | 2 | 5 ± 2.800 | 8 ± 1.240 | 8 ± 1.754 |
| Element-Coverage (statisch) | 2 | 5 ± 3.347 | 12 ± 1.511 | 12 ± 2.215 |
| Flakiness (↓) | 0.000 | 0.000 | 0.000 | 0.000 |
| Laufzeit (s) (↓) | 0.860 | 2.260 ± 3.148 | 15.390 ± 4.824 | 15.720 ± 4.845 |
| Judge: Correctness (↑) | 0.500 | 0.614 ± 0.192 | 0.768 ± 0.180 | 0.761 ± 0.202 |
| Judge: Appropriateness (↑) | 0.400 | 0.776 ± 0.139 | 0.728 ± 0.121 | 0.696 ± 0.148 |
| Judge: Hallucination (↓) | n/a | 0.212 ± 0.201 | 0.082 ± 0.136 | 0.070 ± 0.131 |
| Judge: Readability (↑) | 0.500 | 0.702 ± 0.125 | 0.812 ± 0.133 | 0.796 ± 0.171 |
| ISO: Correctness (↑) | 0.750 | 0.775 ± 0.121 | 0.688 ± 0.060 | 0.679 ± 0.097 |
| ISO: Completeness (↑) | 0.400 | 0.048 ± 0.137 | 0.216 ± 0.106 | 0.208 ± 0.099 |
| ISO: Appropriateness (↑) | 0.400 | 0.776 ± 0.139 | 0.728 ± 0.121 | 0.696 ± 0.148 |
| ISO: Functional Suitability (↑) | 0.517 | 0.533 ± 0.087 | 0.544 ± 0.039 | 0.527 ± 0.078 |

n/a = für diese Pipeline nicht anwendbar. ± x = Std über die Wiederholungen.

## Auffälligkeiten (über die Wiederholungen)

**Skript_L**
- Instabil: in 39/50 Läufen alle Tests grün
- Unterschiedliche Testanzahl pro Lauf: 2–8
- Hohe Varianz bei gen_time_s: 33.618 ± 27.3378
- Hohe Varianz bei exercised_coverage: 4.72 ± 2.7997
- Hohe Varianz bei element_coverage: 4.94 ± 3.3467
- Hohe Varianz bei duration_s: 2.263 ± 3.1478
- Hohe Varianz bei hallucination: 0.212 ± 0.2007
- Hohe Varianz bei iso_completeness: 0.048 ± 0.1374

**Skript_S**
- Instabil: in 1/50 Läufen alle Tests grün
- Hohe Varianz bei gen_time_s: 49.708 ± 36.0342
- Hohe Varianz bei hallucination: 0.082 ± 0.1364
- Hohe Varianz bei iso_completeness: 0.216 ± 0.1057

**Skript_H**
- Instabil: in 3/50 Läufen alle Tests grün
- Hohe Varianz bei gen_time_s: 46.974 ± 61.9669
- Hohe Varianz bei hallucination: 0.07 ± 0.1313
- Hohe Varianz bei iso_completeness: 0.208 ± 0.0986

## Detail je Pipeline

### Skript_C (crawler) · 1×
- Generierungszeit: 3.840 s · Modell: `(none)` · Provider: `crawler`
- Meta: `{'n_states': 3, 'n_edges': 2, 'n_scenarios': 4, 'element_coverage': 1, 'discovered_elements': 4, 'crawl_time_s': 3.63, 'locator_catalog': [{'label': 'New Todo Input', 'role': 'textbox', 'locator': 'page.get_by_test_id("text-input")', 'url': 'http://localhost:8080/?'}, {'label': 'on', 'role': 'generic', 'locator': 'page.get_by_test_id("toggle-all")', 'url': 'http://localhost:8080/?'}, {'label': 'Active', 'role': 'link', 'locator': 'page.get_by_role("link", name="Active").first', 'url': 'http://localhost:8080/?'}, {'label': 'Completed', 'role': 'link', 'locator': 'page.get_by_role("link", name="Completed").first', 'url': 'http://localhost:8080/?'}], 'routes': ['http://localhost:8080/#/active?', 'http://localhost:8080/#/completed?', 'http://localhost:8080/?']}`
- Judge-Begründungen:
  - **hallucination**: n/a (für diese Pipeline nicht anwendbar)
  - **readability**: Test names like test_scenario_1 are generic and do not clearly convey purpose, though docstrings partially describe actions. Structure is logical and aligns with the input's routes. Comments are redundant, repeating the same smoke assertion explanation across all tests. No dead code is present, but assertions are weak, only checking body attachment rather than verifying the 'New Todo Input' or 'Active'/'Completed' routes.
  - **correctness**: The test suite covers the discovered routes (http://localhost:8080/, /#/active, /#/completed) and includes a transition filling 'New Todo Input' with 'Test' + Enter, which aligns with the known application surface. However, the assertions are weak and generic—each test only checks that the body is attached, which does not meaningfully verify the interactions or state changes (e.g., todo creation, filtering). The comments about modal/sidenav overlays are irrelevant to TodoMVC, suggesting boilerpl
  - **appropriateness**: The test suite covers plausible routes from the discovered application surface (root, /#/active, /#/completed) and includes a basic interaction with the 'New Todo Input' by filling and pressing Enter. However, it falls short on locator robustness and assertion quality. It relies on `get_by_test_id` rather than user-facing locators like `get_by_placeholder` for the input, and the assertions are weak smoke checks (`expect(page.locator('body')).to_be_attached()`) that do not verify the actual appli

<details><summary>Skript_C — Code</summary>

```python
"""Skript_C — autonomously generated Web-UI test suite (traditional crawler).

Target : TodoMVC (React) (http://localhost:8080)
States : 3   Transitions: 2   Crawl time: 3.63s
Generated by the crawler pipeline; no user story was consulted.
"""

import pytest
from playwright.sync_api import Page, expect


def test_scenario_1(page: Page) -> None:
    """goto http://localhost:8080/ -> fill 'New Todo Input' = 'Test' + Enter"""
    page.goto("http://localhost:8080/")
    page.wait_for_load_state()
    page.get_by_test_id("text-input").fill("Test")
    page.get_by_test_id("text-input").press("Enter")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_2(page: Page) -> None:
    """goto http://localhost:8080/"""
    page.goto("http://localhost:8080/")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_3(page: Page) -> None:
    """goto http://localhost:8080/#/active"""
    page.goto("http://localhost:8080/#/active")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()


def test_scenario_4(page: Page) -> None:
    """goto http://localhost:8080/#/completed"""
    page.goto("http://localhost:8080/#/completed")
    page.wait_for_load_state()
    # Robust smoke assertion: body present in the DOM (avoids false "hidden"
    # failures when a modal/sidenav overlay is open at the end of the scenario).
    expect(page.locator("body")).to_be_attached()
```
</details>

### Skript_L (llm_agent) · 50×
- Generierungszeit: 27.770 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_todo_mvc_link_navigates_to_todomvc[chromium]:       - text: Fady
- Meta: `{'agent_steps': 11, 'pages_observed': 1, 'user_story_used': False, 'browser_backend': 'inprocess', 'grounded_agent': False, 'postprocess_fixes': []}`
- Judge-Begründungen:
  - **readability**: The test names are descriptive and clearly convey their purpose (e.g., 'test_homepage_loads_with_todo_input', 'test_todo_input_accepts_text'). The structure is logical and easy to follow, with each test focusing on a single behavior. However, the tests do not fully align with the known application surface: they include checks for a 'TodoMVC' link and external navigation, which are not part of the discovered routes or UI elements (Active, Completed, New Todo Input). This introduces unnecessary co
  - **correctness**: The test suite aligns well with the discovered application surface, specifically targeting the 'New Todo Input' element and verifying its visibility, text acceptance, and clearing behavior. The assertions logically follow from the actions performed, such as filling the input and checking its value. However, the suite includes a test for a 'TodoMVC' link, which is not part of the known UI elements or routes, introducing a minor inconsistency. Overall, the tests are coherent and relevant to the in
  - **appropriateness**: The tests exercise plausible user-facing flows on the TodoMVC application, such as loading the homepage, interacting with the New Todo Input, and verifying the TodoMVC link. The locators are robust and appropriate, using get_by_role with accessible names like 'New Todo Input' and 'TodoMVC', and web-first assertions like to_be_visible and to_have_value. However, the tests do not cover the known routes (#/active, #/completed) or UI elements (Active, Completed, on) mentioned in the Input, which lim
  - **hallucination**: The output's references to the 'New Todo Input' textbox and the base URL are explicitly confirmed in the Known Application Surface. The 'TodoMVC' link with href 'http://todomvc.com' is not listed in the surface, but it is a plausible and common element in a TodoMVC application, so it is reasonably inferred rather than fabricated. No clearly made-up data-testid values or implausible routes are present. Minor uncertainty arises from the unconfirmed 'TodoMVC' link, but it fits the application conte
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_L — Code</summary>

```python
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8080"


def test_homepage_loads_with_todo_input(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("body")).to_be_attached()
    expect(page.get_by_role("textbox", name="New Todo Input")).to_be_visible()
    expect(page.get_by_role("link", name="TodoMVC")).to_be_visible()


def test_todo_input_accepts_text(page: Page):
    page.goto(BASE_URL)
    todo_input = page.get_by_role("textbox", name="New Todo Input")
    expect(todo_input).to_be_visible()
    todo_input.fill("Buy milk")
    expect(todo_input).to_have_value("Buy milk")


def test_todo_input_can_be_cleared(page: Page):
    page.goto(BASE_URL)
    todo_input = page.get_by_role("textbox", name="New Todo Input")
    todo_input.fill("Buy milk")
    expect(todo_input).to_have_value("Buy milk")
    todo_input.fill("")
    expect(todo_input).to_have_value("")


def test_todomvc_link_navigates_to_external_site(page: Page):
    page.goto(BASE_URL)
    link = page.get_by_role("link", name="TodoMVC")
    expect(link).to_be_visible()
    expect(link).to_have_attribute("href", "http://todomvc.com")
```
</details>

### Skript_S (llm_agent_story) · 50×
- Generierungszeit: 47.250 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_active_filter_shows_only_uncompleted_todos[chromium]:       - /url: http://todomvc.com
- Meta: `{'agent_steps': 13, 'pages_observed': 1, 'user_story_used': True, 'browser_backend': 'inprocess', 'grounded_agent': False, 'postprocess_fixes': [], 'runtime_repair_rounds': 1, 'ssr_before_repair': 0.5714, 'ssr_after_repair': 0.5714, 'runtime_repair_time_s': 49.32}`
- Judge-Begründungen:
  - **correctness**: The test suite covers all seven user stories with appropriate sequences and assertions for most acceptance criteria. It correctly uses the discovered UI elements (e.g., 'New Todo Input', 'Active', 'Completed') and verifies counter updates, filter behavior, editing via double-click, deletion, and clearing completed todos. However, it misses asserting the strikethrough visual state for completed todos (US-2), does not verify the placeholder text 'What needs to be done?' (US-1), and the active/comp
  - **appropriateness**: The tests cover all seven user stories from the Input, targeting the exact scenarios described. Locators are generally user-facing, using get_by_role and get_by_text for elements like the 'New Todo Input' textbox, 'Active' and 'Completed' links, and 'Clear completed' button, aligning with the known application surface. Web-first assertions like to_be_visible, to_have_count, and to_contain_text validate expected outcomes such as item visibility, counter updates, and filter behavior. However, some
  - **hallucination**: All referenced UI elements, routes, and selectors are plausibly grounded. The base URL 'http://localhost:8080' matches the Input. The 'New Todo Input' textbox name is explicitly listed in the Known Application Surface. The 'Active' and 'Completed' filters are named in both the User Stories and the Known Application Surface. The 'Clear completed' button is directly referenced in US-7. Standard TodoMVC conventions are used for the checkbox, the edit input (nth textbox), the 'li' locator for todo i
  - **readability**: The test names are highly descriptive and align well with the user stories (e.g., 'test_add_todo_updates_list_and_counter' for US-1, 'test_mark_todo_completed_strikes_text_and_decrements_counter' for US-2). The structure is clear and logical, with each test following a consistent setup-action-assert pattern. No unnecessary comments clutter the code, and there is no dead code or unused variables. The tests correctly reference known UI elements like 'New Todo Input', 'Active', and 'Completed' filt
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_S — Code</summary>

```python
from playwright.sync_api import Page, expect


def test_add_todo_updates_list_and_counter(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    expect(input_field).to_be_attached()

    input_field.fill("Buy milk")
    input_field.press("Enter")

    todo_item = page.get_by_text("Buy milk")
    expect(todo_item.first).to_be_visible()

    footer = page.locator("body")
    expect(footer).to_contain_text("1 item left")


def test_mark_todo_completed_strikes_text_and_decrements_counter(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")

    checkbox = page.get_by_role("checkbox").first
    checkbox.check()

    todo_item = page.get_by_text("Buy milk").first
    expect(todo_item).to_be_visible()

    expect(page.locator("body")).to_contain_text("0 items left")


def test_active_filter_shows_only_uncompleted_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    input_field.fill("Walk dog")
    input_field.press("Enter")

    page.get_by_role("checkbox").first.check()

    active_filter = page.get_by_role("link", name="Active")
    expect(active_filter.first).to_be_attached()
    active_filter.first.click()

    expect(page.get_by_text("Buy milk").first).to_be_visible()
    expect(page.get_by_text("Walk dog")).to_have_count(0)


def test_completed_filter_shows_only_completed_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    input_field.fill("Walk dog")
    input_field.press("Enter")

    page.get_by_role("checkbox").first.check()

    completed_filter = page.get_by_role("link", name="Completed")
    expect(completed_filter.first).to_be_attached()
    completed_filter.first.click()

    expect(page.get_by_text("Buy milk").first).to_be_visible()
    expect(page.get_by_text("Walk dog")).to_have_count(0)


def test_double_click_todo_text_allows_editing(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")

    todo_text = page.get_by_text("Buy milk").first
    todo_text.dblclick()

    edit_input = page.get_by_role("textbox").nth(1)
    expect(edit_input).to_be_attached()

    edit_input.fill("Buy oat milk")
    edit_input.press("Enter")

    expect(page.get_by_text("Buy oat milk").first).to_be_visible()


def test_delete_todo_removes_it_from_list(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")

    todo_item = page.locator("li").filter(has_text="Buy milk").first
    todo_item.hover()

    destroy_button = todo_item.locator("button").first
    expect(destroy_button).to_be_attached()
    destroy_button.click()

    expect(page.get_by_text("Buy milk")).to_have_count(0)


def test_clear_completed_removes_only_completed_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    input_field.fill("Walk dog")
    input_field.press("Enter")

    page.get_by_role("checkbox").first.check()

    clear_button = page.get_by_role("button", name="Clear completed")
    expect(clear_button.first).to_be_attached()
    clear_button.first.click()

    expect(page.get_by_text("Buy milk")).to_have_count(0)
    expect(page.get_by_text("Walk dog").first).to_be_visible()
```
</details>

### Skript_H (hybrid) · 50×
- Generierungszeit: 21.220 s · Modell: `kimi-k2.7-code:cloud` · Provider: `ollama`
- Erster Test-Fehler: test_us7_clear_completed_todos[chromium]:       - /url: http://todomvc.com
- Meta: `{'agent_steps': 5, 'pages_observed': 1, 'user_story_used': True, 'browser_backend': 'inprocess', 'grounded_agent': True, 'postprocess_fixes': [], 'grounded_routes': 3, 'grounded_locators': 4, 'refined_from': 'crawler', 'exploration_time_s': 3.63, 'input_element_coverage': 1, 'domain_context_used': False, 'runtime_repair_rounds': 1, 'ssr_before_repair': 0.8571, 'ssr_after_repair': 0.8571, 'runtime_repair_time_s': 29.83}`
- Judge-Begründungen:
  - **hallucination**: The Actual Output references UI elements and routes that align well with the Input's User Stories and Known Application Surface. The 'New Todo Input' textbox, 'Active' and 'Completed' filters, and 'Clear completed' button are all explicitly mentioned in the Input or implied by the User Stories. The use of standard Playwright locators like 'checkbox' and 'textbox' is appropriate for the application type. However, the test for US-6 (delete todo) does not interact with any delete-specific UI elemen
  - **readability**: The test names are descriptive and align with the user stories (e.g., test_us1_add_todo, test_us2_mark_todo_completed). The structure is logical and easy to follow. However, the assertions are weak and do not properly verify the acceptance criteria. For example, in test_us2_mark_todo_completed, it checks if the body is attached instead of verifying the todo is marked as completed (e.g., through a CSS class or strikethrough). Similarly, in test_us6_delete_todo, it does not verify the todo is actu
  - **correctness**: The tests cover the basic sequence of actions for each user story, but assertions are weak and often do not correspond to acceptance criteria. For US-1, the footer counter is not actually checked for the number of open tasks; it only asserts the body is attached. For US-2, there is no assertion that the todo is displayed as completed (e.g., strikethrough) or that the counter decreases. US-3 and US-4 do not verify that completed or active todos are hidden when filtering. US-5 correctly checks the
  - **appropriateness**: The tests target the relevant user stories but exhibit significant shortcomings in locators and assertions. While user-facing locators like get_by_role and get_by_text are used for inputs and filters, several tests fall back to page.locator('body') (e.g., in US-1, US-2, US-6), which is not a user-facing locator and fails to validate specific elements like the footer counter or completed state. Assertions predominantly use to_be_attached() instead of web-first assertions that validate expected ou
  - **_hinweis**: Begründungen stammen aus einem von 50 Läufen; die Scores sind Mittelwerte.

<details><summary>Skript_H — Code</summary>

```python
from playwright.sync_api import Page, expect


def test_us1_add_todo(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    expect(input_field).to_be_attached()
    input_field.fill("Buy milk")
    input_field.press("Enter")
    todo_item = page.get_by_text("Buy milk")
    expect(todo_item.first).to_be_visible()
    footer_counter = page.locator("body")
    expect(footer_counter).to_be_attached()


def test_us2_mark_todo_completed(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    checkbox = page.get_by_role("checkbox").first
    expect(checkbox).to_be_attached()
    checkbox.check()
    completed_todo = page.locator("body")
    expect(completed_todo).to_be_attached()


def test_us3_filter_active_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    input_field.fill("Walk dog")
    input_field.press("Enter")
    active_filter = page.get_by_role("link", name="Active")
    expect(active_filter).to_be_visible()
    active_filter.click()
    active_todo = page.get_by_text("Buy milk")
    expect(active_todo.first).to_be_visible()


def test_us4_filter_completed_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    checkbox = page.get_by_role("checkbox").first
    checkbox.check()
    completed_filter = page.get_by_role("link", name="Completed")
    expect(completed_filter).to_be_visible()
    completed_filter.click()
    completed_todo = page.get_by_text("Buy milk")
    expect(completed_todo.first).to_be_visible()


def test_us5_edit_todo_text(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    todo_text = page.get_by_text("Buy milk").first
    todo_text.dblclick()
    edit_input = page.get_by_role("textbox").nth(1)
    expect(edit_input).to_be_attached()
    edit_input.fill("Buy oat milk")
    edit_input.press("Enter")
    updated_todo = page.get_by_text("Buy oat milk")
    expect(updated_todo.first).to_be_visible()


def test_us6_delete_todo(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    todo_item = page.locator("body")
    expect(todo_item).to_be_attached()


def test_us7_clear_completed_todos(page: Page):
    page.goto("http://localhost:8080")
    input_field = page.get_by_role("textbox", name="New Todo Input")
    input_field.fill("Buy milk")
    input_field.press("Enter")
    input_field.fill("Walk dog")
    input_field.press("Enter")
    checkbox = page.get_by_role("checkbox").first
    checkbox.check()
    clear_button = page.get_by_text("Clear completed")
    expect(clear_button.first).to_be_visible()
    clear_button.first.click()
    remaining_todo = page.get_by_text("Walk dog")
    expect(remaining_todo.first).to_be_visible()
```
</details>
