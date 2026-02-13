# Category filtering and relevance scoring

import re
from config import ELECTRONICS_TOKENS, MATERIALS_TOKENS


def infer_intent(keyword: str) -> str:
    # Determine if keyword is materials or electronics based on token matching
    k = keyword.lower()
    m = sum(1 for t in MATERIALS_TOKENS if t in k)
    e = sum(1 for t in ELECTRONICS_TOKENS if t in k)

    if m > e:
        return "materials"
    if e > m:
        return "electronics"
    return "materials"  # Default to materials


def token_hits(text: str, token_set: set[str]) -> int:
    # Count how many tokens from token_set appear in text
    t = text.lower()
    return sum(1 for tok in token_set if tok in t)


def should_filter_out(intent: str, keyword: str, title: str) -> bool:
    # Determine if a product should be filtered out based on category mismatch
    kw = keyword.lower().strip()
    t = title.lower().strip()

    e_hits = token_hits(t, ELECTRONICS_TOKENS)
    m_hits = token_hits(t, MATERIALS_TOKENS)

    if intent == "materials":
        # Filter out clear electronics
        if e_hits >= 2 and m_hits == 0:
            return True
        # Specific wood/electronics conflict
        if "wood" in kw and any(
            x in t for x in [
                "argb", "rgb", "mid tower", "motherboard",
                "rtx", "ryzen", "intel", "radeon"
            ]
        ):
            return True
        return False

    if intent == "electronics":
        # Filter out clear materials
        if m_hits >= 2 and e_hits == 0:
            return True
        return False

    return False


def normalize_words(s: str) -> list[str]:
    # Normalize text to list of words
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]+", " ", s)
    return [w for w in s.split() if w]


def relevance_score(keyword: str, title: str) -> float:
    # Calculate relevance score between keyword and title
    # Higher is better (0.0 to 1.25+)
    kw_words = normalize_words(keyword)
    if not kw_words:
        return 0.0

    t_words = normalize_words(title)
    if not t_words:
        return 0.0

    kw_set = set(kw_words)
    t_set = set(t_words)

    # Word overlap ratio
    overlap = len(kw_set & t_set)
    ratio = overlap / max(len(kw_set), 1)

    # Bonus if exact phrase appears
    phrase_bonus = 0.25 if " ".join(kw_words) in title.lower() else 0.0

    return ratio + phrase_bonus
