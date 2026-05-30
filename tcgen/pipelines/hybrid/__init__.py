"""Hybrid refiner pipeline (Skript_H, Methode 2).

Takes the traditional crawler artefact (Skript_C) and asks an LLM to improve it
along three explicit axes: robust locators, requirement-derived assertions, and
readability/maintainability. Kept fully separate from Methode 1 so it can be
switched on as the second increment without touching the baseline pipelines.
"""

from tcgen.pipelines.hybrid.refiner import HybridRefiner, generate

__all__ = ["HybridRefiner", "generate"]
