# Architectural Review Agent

An agent that performs **local tool calling**, parses **architecture review documentation** (Markdown), and invokes an **LLM** to provide detailed feedback. The orchestration includes:

- **Input policy** – evaluate and allow/deny the incoming document
- **Output policy** – evaluate and allow/deny the response before returning
- **Tool calling** – local tools (registry + invocation)
- **LLM calling** – OpenAI-compatible API (Ollama, LiteLLM, vLLM, etc.)
- **Failure mode analysis** – categorize and record failures for observability

## Project structure

```
agentic-arch-review/
├── pyproject.toml
├── requirements.txt
├── .env.example
├── src/
│   └── arch_review_agent/
│       ├── __init__.py
│       ├── main.py              # CLI entry
│       ├── config.py            # Settings (pydantic-settings)
│       ├── orchestration/       # Pipeline & orchestrator
│       │   ├── orchestrator.py
│       │   └── pipeline.py
│       ├── policies/            # Input & output policy
│       │   ├── input_policy.py
│       │   └── output_policy.py
│       ├── tools/               # Local tool registry & base
│       │   ├── base.py
│       │   └── registry.py
│       ├── llm/                 # LLM client (OpenAI-compatible HTTP)
│       │   └── client.py
│       ├── parsing/             # Markdown parser for arch docs
│       │   └── markdown_parser.py
│       └── failure_analysis/    # Failure mode analysis
│           └── analyzer.py
├── samples/
│   └── sample_architecture.md
└── tests/
    └── test_orchestration.py
```

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   
   pip install -r requirements.txt
   ```

   If you hit SSL errors with a corporate PyPI mirror, use the public index:
   `pip install --index-url https://pypi.org/simple/ --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt`

2. Copy `.env.example` to `.env` and set your LLM endpoint (e.g. [Ollama](https://ollama.ai/) with an OpenAI-compatible server, or LiteLLM).

3. **Run the agent** (so your latest code changes are used):

   From the **project root** (where `run.py` lives), use:

   ```bash
   python run.py
   python run.py samples/sample_architecture.md
   ```

   The first line printed will show which `arch_review_agent` is loaded; it should point at `.../agentic-arch-review/src/arch_review_agent`.  

   **In Cursor (or any editor):** If you run `main.py` directly or use `python -m arch_review_agent.main`, the process does *not* run `run.py`, so Python loads the package from site-packages (your edits in `src/` are ignored). See [docs/WHY_RUN_PY.md](docs/WHY_RUN_PY.md) for the exact explanation. To see which code is loading, run `python scripts/show_import_path.py`.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BASE_URL` | OpenAI-compatible API base URL | `http://localhost:11434/v1` |
| `LLM_API_KEY` | API key (optional for local Ollama) | — |
| `LLM_MODEL` | Model name | `llama3.2` |
| `ENABLE_INPUT_POLICY` | Run input policy check | `true` |
| `ENABLE_OUTPUT_POLICY` | Run output policy check | `true` |
| `ENABLE_FAILURE_ANALYSIS` | Run failure analysis | `true` |

## Implementation status

The project is a **boilerplate** with clear extension points. Remaining work (marked with `TODO` in code):

- **Orchestrator**: Wire pipeline stages (load doc → input policy → parse → tools → LLM → output policy → failure analysis).
- **Policies**: Implement input/output checks (size, format, content filters).
- **Tools**: Implement and register concrete tools; call them from the pipeline.
- **LLM client**: Implement `chat()` with `httpx` and integrate into the pipeline.
- **Parsing**: Implement `parse_architecture_doc()` to produce a structured representation.
- **Failure analysis**: Refine categorization and attach results to the pipeline context.

## Dependencies (FOSS)

- **pydantic** / **pydantic-settings** – config and schemas
- **python-dotenv** – env loading
- **httpx** – HTTP client for LLM API
- **markdown** – Markdown parsing

## License

