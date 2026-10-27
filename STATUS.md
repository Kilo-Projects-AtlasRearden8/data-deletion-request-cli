# STATUS

## What was built

A local-first Python CLI, `data-deletion-request-cli`, that drafts GDPR and CCPA
data-deletion and opt-out letters from Jinja2 templates. It prints the letter
to stdout (or a file) and never sends it automatically. Optional LLM polishing
is available through any OpenAI-compatible chat endpoint, defaulting to Ollama
(`http://localhost:11434/v1/chat/completions`).

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Examples:

```bash
# GDPR deletion letter, printed to stdout
python -m data_deletion_cli \
  --regulation gdpr --type deletion \
  --name "Ada Lovelace" --email "ada@example.test" \
  --address "123 Example Lane, London" --company "Example Corp"

# CCPA opt-out letter saved to a file
python -m data_deletion_cli \
  --regulation ccpa --type opt-out \
  --name "Ada Lovelace" --email "ada@example.test" \
  --company "Example Corp" --output ccpa_opt_out.txt

# Optional LLM polishing (default Ollama endpoint)
python -m data_deletion_cli \
  --regulation gdpr --type deletion --name "Ada Lovelace" \
  --email "ada@example.test" --company "Example Corp" --polish
```

Run the tests:

```bash
pip install -e ".[dev]"
pytest
```

## Verification results

- `pytest`: 6 passed (template rendering: GDPR deletion, CCPA deletion, CCPA
  opt-out, empty-address handling, GDPR+opt-out fallback, signature ending).
- CLI smoke-tested: GDPR deletion, CCPA deletion, CCPA opt-out, output-to-file,
  gdpr+opt-out rejection (exit 2), and LLM polishing with an unreachable
  endpoint (prints warning, falls back to original draft, exit 0).
- Package installs cleanly via `pip install -e .` and `pip install -e ".[dev]"`.

## Known gaps

- No console-script entry point declared in `pyproject.toml`; invoke via
  `python -m data_deletion_cli`.
- No lint/typecheck tooling configured (no ruff/mypy in this environment).
- LLM polishing is best-effort and requires a running OpenAI-compatible
  endpoint; it is not tested against a live LLM (no secrets/keys stored).
- Templates are English-only.

## Credits

Built and maintained by Asdale Dynamics, LLC. MIT License.
Copyright (c) 2026 Asdale Dynamics, LLC.
