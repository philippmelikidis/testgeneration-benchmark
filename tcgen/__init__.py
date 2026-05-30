"""LLM vs. traditional Web-UI test-case generation benchmark.

Package layout:
    tcgen.llm            LLM provider abstraction (Ollama default, OpenAI optional)
    tcgen.pipelines      script generators: crawler (Skript_C), llm_agent (Skript_L),
                         hybrid refiner (Skript_H, Methode 2)
    tcgen.runner         pytest-based execution + metric suite (objective + DeepEval)
    tcgen.orchestration  experiment runner, data models, results persistence
"""

__version__ = "0.1.0"
