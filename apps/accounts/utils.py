def normalize_phone_number(phone_number):
    raw = (phone_number or "").strip()
    has_plus = raw.startswith("+")
    digits = "".join(char for char in raw if char.isdigit())
    if not digits:
        return ""
    return f"+{digits}" if has_plus else digits


def phone_number_candidates(phone_number):
    normalized = normalize_phone_number(phone_number)
    digits = "".join(char for char in normalized if char.isdigit())
    candidates = {normalized, digits}

    if digits.startswith("998"):
        candidates.add(f"+{digits}")
        candidates.add(digits[3:])
    elif len(digits) == 9:
        candidates.add(f"998{digits}")
        candidates.add(f"+998{digits}")

    return {value for value in candidates if value}
