import re

def clean_text(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value or None

def find_email(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None

def find_phone(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"(\+?\d[\d\-\(\)\s]{8,}\d)", text)
    return match.group(0).strip() if match else None