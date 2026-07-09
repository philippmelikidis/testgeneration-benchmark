"""Hybrid pipeline (Skript_H, Methode 2 — grounded agent).

Skript_H is a LIVE LLM agent seeded with the traditional crawler's state graph
(routes + verified locator catalog): it explores the app itself but stays
grounded in the crawler's real selectors. Kept separate from Methode 1 so the
baseline pipelines are untouched.
"""

from tcgen.pipelines.hybrid.refiner import HybridRefiner, generate

__all__ = ["HybridRefiner", "generate"]
