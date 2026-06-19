# Multi-Modal Evidence Review Pipeline

Python pipeline skeleton for the HackerRank Orchestrate June 2026 challenge.

## Layout

```text
code/
├── main.py                     # Process dataset/claims.csv -> output.csv
├── requirements.txt            # Python dependencies
├── scripts/
│   └── check_setup.py          # Verify deps + API keys
├── pipeline/
│   ├── config.py               # Paths, allowed values, output schema
│   ├── settings.py             # API keys and model settings from env
│   ├── models.py               # ClaimInput, ClaimOutput, context dataclasses
│   ├── data_loader.py          # CSV + image path parsing
│   ├── evidence.py             # Evidence requirement lookup
│   ├── user_history.py         # User history lookup + risk flag merge
│   ├── verifier.py             # Placeholder verifier (replace with VLM/LLM)
│   ├── processor.py            # Orchestrates claim processing
│   └── output_writer.py        # Writes output.csv with required columns
└── evaluation/
    └── main.py                 # Evaluate against sample_claims.csv
```

## Requirements

- Python 3.10+

## Setup

### 1. Create a virtual environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r code/requirements.txt
```

### 2. Configure API keys

Copy the example env file:

```bash
cp .env.example .env
```

Edit `.env` and add at least one provider key:

```bash
OPENAI_API_KEY=sk-...
# and/or
ANTHROPIC_API_KEY=sk-ant-...

DEFAULT_PROVIDER=openai
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

Secrets are read from environment variables only. `.env` is gitignored and must never be committed.

You can also export keys directly in your shell instead of using `.env`:

```bash
export OPENAI_API_KEY=sk-...
export DEFAULT_PROVIDER=openai
```

### 3. Verify setup

```bash
python code/scripts/check_setup.py
```

To require a specific provider:

```bash
python code/scripts/check_setup.py --provider openai
python code/scripts/check_setup.py --provider anthropic
```

## Run on test claims

From the repository root:

```bash
python code/main.py
```

Optional flags:

```bash
python code/main.py \
  --claims dataset/claims.csv \
  --output output.csv \
  --user-history dataset/user_history.csv \
  --evidence-requirements dataset/evidence_requirements.csv
```

## Evaluate on sample claims

```bash
python code/evaluation/main.py
```

The skeleton verifier returns placeholder predictions, so accuracy will be low until visual analysis is implemented.

## Using settings in your verifier

```python
from pipeline.settings import load_settings

settings = load_settings()
api_key = settings.api_key_for_provider(settings.default_provider)
model = settings.model_for_provider(settings.default_provider)
```

## Next steps

1. Replace `ClaimVerifier` in `pipeline/verifier.py` with a VLM/LLM-backed implementation.
2. Use `ClaimContext.evidence_requirements` and `ClaimContext.user_history` in prompts and rule layers.
3. Expand `evaluation/` with strategy comparison and `evaluation_report.md`.

## Secrets

Supported environment variables:

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | One provider required | OpenAI vision/chat API |
| `ANTHROPIC_API_KEY` | One provider required | Anthropic vision/chat API |
| `DEFAULT_PROVIDER` | No | `openai` or `anthropic` (default: `openai`) |
| `OPENAI_MODEL` | No | Default: `gpt-4o` |
| `ANTHROPIC_MODEL` | No | Default: `claude-sonnet-4-20250514` |
| `REQUEST_TIMEOUT_SECONDS` | No | Default: `120` |
| `MAX_RETRIES` | No | Default: `2` |

Never hardcode secrets in the repository.
