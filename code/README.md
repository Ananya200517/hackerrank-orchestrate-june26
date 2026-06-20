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
│   ├── prompts.py              # VLM system/user prompts + JSON parsing
│   ├── vlm_client.py           # OpenAI / Anthropic vision API clients
│   ├── image_utils.py          # Base64 image encoding
│   ├── verifier.py             # VLMClaimVerifier + StubClaimVerifier
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
python3 code/main.py
```

Use the stub verifier (no API calls):

```bash
python3 code/main.py --stub
```

Use a specific provider:

```bash
python3 code/main.py --provider openai
python3 code/main.py --provider anthropic
```

Process only the first N rows while iterating:

```bash
python3 code/main.py --limit 5
```

## Evaluate on sample claims

```bash
python3 code/evaluation/main.py
python3 code/evaluation/main.py --limit 5
python3 code/evaluation/main.py --provider anthropic
python3 code/evaluation/main.py --stub
```

## VLM verifier

`VLMClaimVerifier` sends each claim's images, conversation, evidence requirements, and user history to a vision model and parses a structured JSON decision.

Flow:

```text
ClaimContext -> prompts.py -> vlm_client.py -> parse JSON -> post-process -> ClaimOutput
```

The processor still merges `user_history` risk flags after the model response.

Key files:

- `pipeline/prompts.py` — system prompt with step-by-step decision rubric
- `pipeline/response_postprocess.py` — enum normalizations and risk-flag cleanup
- `pipeline/vlm_client.py` — OpenAI and Anthropic vision calls + usage stats
- `evaluation/prompt_tuning_report.md` — baseline vs tuned accuracy notes

### Prompt tuning workflow

```bash
python3 code/evaluation/main.py --verbose
python3 code/evaluation/main.py --limit 5 --verbose
```

Edit `pipeline/prompts.py` and re-run evaluation to compare field accuracy.

## Next steps

1. Tune prompts and compare at least two strategies/models in `evaluation/`.
2. Write `evaluation/evaluation_report.md` with metrics, cost, and latency.
3. Run full `dataset/claims.csv` and produce final `output.csv`.

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
