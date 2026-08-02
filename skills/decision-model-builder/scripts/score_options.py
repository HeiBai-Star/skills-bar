#!/usr/bin/env python3
"""Rank options from anchored 0-100 scores and expose weight breakpoints."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> None:
    raise ValueError(message)


def load_model(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read valid JSON from {path}: {exc}")

    criteria = data.get("criteria")
    options = data.get("options")
    if not isinstance(criteria, list) or not criteria:
        fail("'criteria' must be a non-empty list")
    if not isinstance(options, list) or len(options) < 2:
        fail("'options' must contain at least two alternatives")

    seen_ids: set[str] = set()
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict):
            fail(f"criterion {index} must be an object")
        criterion_id = criterion.get("id")
        weight = criterion.get("weight")
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            fail(f"criterion {index} needs a non-empty string 'id'")
        if criterion_id in seen_ids:
            fail(f"duplicate criterion id: {criterion_id}")
        seen_ids.add(criterion_id)
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            fail(f"weight for '{criterion_id}' must be numeric")
        if not math.isfinite(weight) or weight < 0:
            fail(f"weight for '{criterion_id}' must be finite and non-negative")

    if sum(float(c["weight"]) for c in criteria) <= 0:
        fail("at least one criterion weight must be positive")

    seen_names: set[str] = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            fail(f"option {index} must be an object")
        name = option.get("name")
        scores = option.get("scores")
        if not isinstance(name, str) or not name.strip():
            fail(f"option {index} needs a non-empty string 'name'")
        if name in seen_names:
            fail(f"duplicate option name: {name}")
        seen_names.add(name)
        if not isinstance(scores, dict):
            fail(f"option '{name}' needs a 'scores' object")
        missing = seen_ids - set(scores)
        extra = set(scores) - seen_ids
        if missing or extra:
            fail(f"option '{name}' score keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
        for criterion_id, score in scores.items():
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                fail(f"score '{name}.{criterion_id}' must be numeric")
            if not math.isfinite(score) or not 0 <= score <= 100:
                fail(f"score '{name}.{criterion_id}' must be between 0 and 100")

    return criteria, options


def analyze(criteria: list[dict[str, Any]], options: list[dict[str, Any]]) -> dict[str, Any]:
    total_weight = sum(float(c["weight"]) for c in criteria)
    weights = {c["id"]: float(c["weight"]) / total_weight for c in criteria}
    labels = {c["id"]: c.get("label", c["id"]) for c in criteria}

    ranking = []
    for option in options:
        contributions = {
            criterion_id: weights[criterion_id] * float(option["scores"][criterion_id])
            for criterion_id in weights
        }
        ranking.append(
            {
                "name": option["name"],
                "score": sum(contributions.values()),
                "contributions": contributions,
            }
        )
    ranking.sort(key=lambda item: (-item["score"], item["name"]))

    top = next(o for o in options if o["name"] == ranking[0]["name"])
    runner_up = next(o for o in options if o["name"] == ranking[1]["name"])
    breakpoints = []
    for criterion in criteria:
        criterion_id = criterion["id"]
        current = weights[criterion_id]
        direct_gap = float(top["scores"][criterion_id]) - float(runner_up["scores"][criterion_id])
        other_weight = 1.0 - current
        if other_weight <= 1e-12:
            other_gap = 0.0
        else:
            other_gap = sum(
                weights[c["id"]]
                * (float(top["scores"][c["id"]]) - float(runner_up["scores"][c["id"]]))
                for c in criteria
                if c["id"] != criterion_id
            ) / other_weight
        denominator = direct_gap - other_gap
        threshold = None if abs(denominator) <= 1e-12 else -other_gap / denominator
        if threshold is not None and -1e-12 <= threshold <= 1 + 1e-12:
            threshold = min(1.0, max(0.0, threshold))
            breakpoints.append(
                {
                    "criterion": criterion_id,
                    "label": labels[criterion_id],
                    "current_weight": current,
                    "break_even_weight": threshold,
                    "change": threshold - current,
                }
            )

    breakpoints.sort(key=lambda item: (abs(item["change"]), item["criterion"]))
    return {
        "normalized_weights": weights,
        "ranking": ranking,
        "top_vs_runner_up": {
            "top": ranking[0]["name"],
            "runner_up": ranking[1]["name"],
            "score_gap": ranking[0]["score"] - ranking[1]["score"],
            "weight_breakpoints": breakpoints,
        },
    }


def markdown(result: dict[str, Any]) -> str:
    lines = ["# Decision score", "", "## Ranking", "", "| Rank | Option | Score |", "|---:|---|---:|"]
    for index, item in enumerate(result["ranking"], start=1):
        lines.append(f"| {index} | {item['name']} | {item['score']:.2f} |")

    comparison = result["top_vs_runner_up"]
    lines.extend(
        [
            "",
            "## Top vs runner-up",
            "",
            f"{comparison['top']} leads {comparison['runner_up']} by {comparison['score_gap']:.2f} points.",
            "",
            "## Weight breakpoints",
            "",
        ]
    )
    breakpoints = comparison["weight_breakpoints"]
    if not breakpoints:
        lines.append("No single criterion weight between 0% and 100% makes the top two options tie while other weights keep their relative proportions.")
    else:
        lines.extend(["| Criterion | Current | Tie point | Change |", "|---|---:|---:|---:|"])
        for item in breakpoints:
            lines.append(
                f"| {item['label']} | {item['current_weight']:.1%} | "
                f"{item['break_even_weight']:.1%} | {item['change']:+.1%} |"
            )
    lines.extend(
        [
            "",
            "> Interpret breakpoints as local sensitivity only. Scores must be anchored 0–100 interval judgments, and hard constraints must be checked before scoring.",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank alternatives using anchored 0-100 scores and normalized criterion weights.",
        epilog=(
            'Input JSON: {"criteria":[{"id":"value","label":"Value","weight":3}],'
            '"options":[{"name":"A","scores":{"value":80}},{"name":"B","scores":{"value":60}}]}. '
            "All scores must be interval judgments from 0 to 100 where higher is better."
        ),
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to the decision JSON file")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        criteria, options = load_model(args.input)
        result = analyze(criteria, options)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "markdown":
        print(markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
