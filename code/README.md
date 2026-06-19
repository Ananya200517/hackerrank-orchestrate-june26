# Multi-Modal Evidence Review Pipeline

Python pipeline skeleton for the HackerRank Orchestrate June 2026 challenge.

## Layout

```text
code/
├── main.py                     # Process dataset/claims.csv -> output.csv
├── pipeline/
│   ├── config.py               # Paths, allowed values, output schema
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

No third-party dependencies are required for the skeleton.

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

## Next steps

1. Replace `ClaimVerifier` in `pipeline/verifier.py` with a VLM/LLM-backed implementation.
2. Use `ClaimContext.evidence_requirements` and `ClaimContext.user_history` in prompts and rule layers.
3. Expand `evaluation/` with strategy comparison and `evaluation_report.md`.

## Secrets

Read API keys from environment variables only, for example:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Never hardcode secrets in the repository.
