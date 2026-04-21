def clean_string(value: object) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def to_float(value: object) -> float | None:
    cleaned = clean_string(value)
    if cleaned is None:
        return None

    negative = False
    normalized = cleaned.replace(",", "").replace("$", "").replace("%", "")
    if normalized.startswith("(") and normalized.endswith(")"):
        negative = True
        normalized = normalized[1:-1]

    try:
        parsed = float(normalized)
    except ValueError:
        return None

    return -parsed if negative else parsed


def to_bool(value: object) -> bool | None:
    cleaned = clean_string(value)
    if cleaned is None:
        return None

    lowered = cleaned.lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    return None
