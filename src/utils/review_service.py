def get_review_status(
        confidence,
        metadata
):

    if "error" in metadata:
        return "Failed"

    if confidence >= 90:
        return "Completed"

    elif confidence >= 70:
        return "Review Required"

    return "Failed"