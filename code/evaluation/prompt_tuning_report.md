# Prompt Tuning Report

Date: 2026-06-20  
Model: `gpt-4o` (DEFAULT_PROVIDER=openai)  
Dataset: `dataset/sample_claims.csv` (20 labeled rows)

## Summary

Prompt tuning focused on decision-field accuracy (not free-text justifications). A step-by-step rubric was added to `pipeline/prompts.py`, plus light post-processing in `pipeline/response_postprocess.py`.

## Field accuracy comparison

| Field | Baseline prompt | Tuned prompt | Change |
|---|---:|---:|---:|
| evidence_standard_met | 80% | 80% | — |
| risk_flags | 60% | 50% | -10 |
| issue_type | 40% | 75% | +35 |
| object_part | 85% | 85% | — |
| claim_status | 70% | 75% | +5 |
| supporting_image_ids | 70% | 85% | +15 |
| valid_image | 80% | 90% | +10 |
| severity | 40% | 60% | +20 |

Free-text fields (`evidence_standard_met_reason`, `claim_status_justification`) remain 0% exact match — expected, since wording varies while decisions can still be correct.

## Prompt changes

1. **Step-by-step rubric** for evidence sufficiency, claim status, issue/part selection, severity, valid_image, and risk flags
2. **Explicit mismatch patterns** — severity exaggeration, wrong-part contradictions, multi-image identity checks, intact seal vs torn claim
3. **Severity calibration** — avoid defaulting to `high`; reserve for clearly severe damage
4. **Risk flag guidance** — do not emit `user_history_risk` (added by processor); auto-add `manual_review_required` for identity/mismatch flags
5. **Issue type distinctions** — crack vs glass_shatter, stain vs water_damage, broken_part for mirrors/hinges

## Post-processing additions

- Strip `user_history_risk` before processor merge (avoid duplicates)
- Auto-add `manual_review_required` for high-risk visual flags
- Normalize common confusions (keyboard water → stain, mirror crack → broken_part, screen glass_shatter → crack)

## Remaining hard cases

- **Row 8 (hood scratch vs front-end damage)** — still often classified as `not_enough_information` instead of `contradicted`
- **Row 18 (missing contents)** — sometimes `supported` instead of `not_enough_information`
- **Row 20 (torn seal)** — sometimes `supported` instead of `contradicted`
- **Risk flag ordering/exact set** — still sensitive to minor flag differences

## How to iterate

```bash
# Full sample eval
python3 code/evaluation/main.py

# Inspect mismatches
python3 code/evaluation/main.py --verbose

# Test a subset while editing prompts
python3 code/evaluation/main.py --limit 5 --verbose
```

Edit prompts in `code/pipeline/prompts.py`. Keep post-processing minimal — only for stable enum normalizations.

## Operational notes

- Tuned prompts are longer (~29k input tokens for 20 samples vs ~35k baseline — varies by retries)
- Use `--limit` while iterating to control cost
- Compare providers: `python3 code/evaluation/main.py --provider anthropic --verbose`
