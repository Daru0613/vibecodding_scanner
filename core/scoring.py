def score_class(score: int) -> str:
    if score >= 80:
        return "CONFIRMED"
    if score >= 50:
        return "PROBABLE"
    if score >= 30:
        return "POSSIBLE"
    return "UNKNOWN"

