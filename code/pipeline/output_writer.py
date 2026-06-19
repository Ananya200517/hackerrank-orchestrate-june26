from __future__ import annotations

import csv
from pathlib import Path

from pipeline.config import OUTPUT_COLUMNS
from pipeline.models import ClaimOutput


def write_output_csv(outputs: list[ClaimOutput], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for output in outputs:
            writer.writerow(output.to_row())
