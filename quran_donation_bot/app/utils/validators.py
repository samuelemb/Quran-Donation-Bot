def parse_positive_int(raw_value: str) -> int | None:
    if not raw_value:
        return None
    if not raw_value.strip().isdigit():
        return None
    value = int(raw_value.strip())
    return value if value > 0 else None


def has_photo(message_photo: list[object] | None) -> bool:
    return bool(message_photo)
