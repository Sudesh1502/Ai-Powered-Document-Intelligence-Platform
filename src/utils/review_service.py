def get_review_status(
        confidence,
        metadata
):

    if "error" in metadata or not metadata:
        return "Failed"

    if confidence >= 80:       # Was 90 — lowered to auto-index high-quality scans
        return "Completed"

    elif confidence >= 50:     # Was 70 — lowered to allow moderate-quality for review
        return "Needs Review"

    return "Failed"