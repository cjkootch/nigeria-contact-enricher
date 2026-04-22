from __future__ import annotations

import re
import unicodedata


def to_snake_case(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", value)


def normalize_company_name(name: str) -> str:
    cleaned = to_snake_case(name).replace("_", " ")
    suffixes = ["limited", "ltd", "plc", "nig", "nigeria", "services", "company", "co"]
    tokens = [t for t in cleaned.split() if t not in suffixes]
    return " ".join(tokens).strip()
