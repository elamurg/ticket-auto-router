"""Load the hand-labelled golden set (data/golden.jsonl) for evaluation.

Each row on disk has `subject` and `body` separately, but `Classifier.classify`
takes one `text: str`. Combining them happens here, once, so every consumer of
the golden set (the runner, and any future comparison script) gets the same
`text` for the same ticket, instead of each one deciding how to join the two
fields on its own.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from router.domain.models import Category

# src/router/evaluation/dataset.py -> parents[3] is the repository root.
# This assumes the package always runs from inside this checkout, which is
# true for a learning project that is never pip-installed anywhere else;
# a package meant to ship its data separately would need a different
# mechanism (importlib.resources) instead of a path computed like this.
GOLDEN_SET_PATH: Final[Path] = Path(__file__).resolve().parents[3] / "data" / "golden.jsonl"


@dataclass(frozen=True)
class GoldenExample:
    id: str
    text: str
    category: Category


def load_golden_set(path: Path = GOLDEN_SET_PATH) -> list[GoldenExample]:
    """Read every non-blank line of a golden-set JSONL file into GoldenExamples."""
    examples: list[GoldenExample] = []
    with path.open(encoding="utf-8") as golden_file:
        for line in golden_file:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            text = f"{row['subject']}\n\n{row['body']}"
            examples.append(
                GoldenExample(
                    id=row["id"],
                    text=text,
                    category=Category(row["category"]),
                )
            )
    return examples
