from __future__ import annotations


def combine_confidence(*scores: float) -> int:
    clean = [max(0.0, min(1.0, float(score) / 100 if score > 1 else float(score))) for score in scores if score is not None]
    if not clean:
        return 50
    return int(round(sum(clean) / len(clean) * 100))
