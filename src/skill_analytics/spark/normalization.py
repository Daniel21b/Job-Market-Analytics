import hashlib
import re
import unicodedata

_NON_WORD = re.compile(r"[^a-z0-9+#]+")
_SPACE = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = unicodedata.normalize("NFKC", value).lower().strip()
    normalized = _NON_WORD.sub(" ", normalized)
    return _SPACE.sub(" ", normalized).strip() or "unknown"


def composite_join_key(company: str, title: str, location: str) -> str:
    normalized = "|".join(
        (normalize_text(company), normalize_text(title), normalize_text(location))
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
