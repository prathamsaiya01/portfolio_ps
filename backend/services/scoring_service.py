from __future__ import annotations

from typing import Dict, Mapping

from backend.config import get_analysis_thresholds, get_scoring_weights


def clamp_score(value) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if numeric < 0:
        return 0
    if numeric > 100:
        return 100
    return int(round(numeric))


def calculate_overall_score(scores: Mapping[str, object]) -> int:
    weights = get_scoring_weights()
    if not scores:
        return 0

    total_weight = 0.0
    weighted_total = 0.0

    for field_name, weight in weights.items():
        raw_value = scores.get(field_name, 0)
        numeric = clamp_score(raw_value)
        weighted_total += numeric * float(weight)
        total_weight += float(weight)

    if total_weight <= 0:
        return 0

    return clamp_score((weighted_total / total_weight) * 1.0)


def recommendation_for_score(score: object) -> str:
    thresholds = get_analysis_thresholds()
    try:
        numeric = clamp_score(score)
    except Exception:
        numeric = 0

    ignore_max = int(thresholds.get("ignore_max", 64))
    candidate_min = int(thresholds.get("candidate_min", 85))

    if numeric <= ignore_max:
        return "IGNORE"
    if numeric < candidate_min:
        return "REVIEW"
    return "CANDIDATE"
