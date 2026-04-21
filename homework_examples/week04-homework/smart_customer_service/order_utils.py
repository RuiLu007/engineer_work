import re


ORDER_ID_PATTERN = re.compile(r"SN\d{11}", re.IGNORECASE)
STRICT_ORDER_ID_PATTERN = re.compile(r"^SN\d{11}$", re.IGNORECASE)


def normalize_order_id(order_id: str) -> str:
    return order_id.strip().upper()


def extract_order_id(text: str) -> str | None:
    match = ORDER_ID_PATTERN.search(text)
    if not match:
        return None
    return normalize_order_id(match.group(0))


def has_order_id(text: str) -> bool:
    return extract_order_id(text) is not None


def is_valid_order_id(order_id: str) -> bool:
    return STRICT_ORDER_ID_PATTERN.fullmatch(normalize_order_id(order_id)) is not None
