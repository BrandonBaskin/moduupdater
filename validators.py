import re
from typing import Tuple


def is_phone_number(value: str) -> bool:
    return bool(re.fullmatch(r"1-\d{3}-\d{3}-\d{4}", value.strip()))


def is_tty_number(value: str) -> bool:
    v = value.strip()
    if v == "711":
        return True
    # Accept explicit TTY-labeled strings only
    # Examples: "TTY: 1-855-123-4567", "For TTY users, call 1-800-000-0000"
    if re.search(r"(?i)\btty\b", v):
        return True
    # Otherwise, do NOT treat generic phone numbers as TTY
    return False


def is_url(value: str) -> bool:
    v = value.strip()
    # Relaxed: allow bare domains and auto-prefix logic upstream
    return bool(re.fullmatch(r"(?i)(https?://)?(www\.)?[a-z0-9.-]+\.[a-z]{2,}(/\S*)?", v))


def is_address(value: str) -> bool:
    # Heuristic: contains state abbreviation and ZIP
    return bool(re.search(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", value.strip()))


def is_business_hours(value: str) -> bool:
    v = value.lower()
    return ("a.m." in v) or ("p.m." in v)


def is_financial(value: str) -> bool:
    v = value.strip()
    if re.search(r"\$\d", v):
        return True
    phrases = [
        "copay", "coinsurance", "covered at 100%", "no coinsurance",
        "no copayment", "no deductible"
    ]
    return any(p in v.lower() for p in phrases)


def validate_by_type(var_type: str, value: str) -> Tuple[bool, str]:
    """Return (valid, reason_if_invalid)."""
    if not value or not value.strip():
        return False, "empty"
    t = (var_type or "").lower()
    try:
        if t == "phone_number":
            ok = is_phone_number(value)
            return ok, "" if ok else "invalid phone number"
        if t == "tty_number":
            ok = is_tty_number(value)
            return ok, "" if ok else "invalid tty number"
        if t == "url":
            ok = is_url(value)
            return ok, "" if ok else "invalid url"
        if t == "address":
            ok = is_address(value)
            return ok, "" if ok else "invalid address"
        if t == "business_hours":
            ok = is_business_hours(value)
            return ok, "" if ok else "invalid business hours"
        if t == "financial":
            ok = is_financial(value)
            return ok, "" if ok else "invalid financial phrase"
        if t == "date_time":
            # Accept common formats like "January 1, 2026", "1/1/2026", "2026"
            v = value.strip()
            ok = bool(
                re.search(r"\b(19|20)\d{2}\b", v)
                or re.search(r"\b\d{1,2}/\d{1,2}/(19|20)\d{2}\b", v)
                or re.search(r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", v)
            )
            return ok, "" if ok else "invalid date/time"
        if t == "address":
            # reuse existing check, but allow city, ST ZIP minimal
            ok = is_address(value)
            return ok, "" if ok else "invalid address"
        # permissive for others
        return True, ""
    except Exception as e:
        return False, str(e)


