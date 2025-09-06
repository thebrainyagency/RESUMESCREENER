# src/contact_norm.py
import re
from typing import Dict, List, Tuple

HTTP_URL_RE = re.compile(r"https?://[^\s)<>\]]+", re.I)
EMAIL_RE = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.I)

# India-friendly phones: +91-XXXXXXXXXX, 0XXXXXXXXXX, 10-digit, tolerate spaces/dashes
PHONE_RE = re.compile(
    r"(?:(?:\+?91[\s\-]?)|(?:0))?\s*(?:[6-9]\d{9}|\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d)",
    re.I,
)

# partial handles
LINKEDIN_PARTIAL_RE = re.compile(r"\b(?:linkedin\.com/)?in/[A-Za-z0-9\-_.]+/?\b", re.I)
GITHUB_PARTIAL_RE = re.compile(r"\b(?:github\.com/|github/)[A-Za-z0-9\-_.]+/?\b", re.I)

def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        x = x.strip().strip(").,;")
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out

def _canon_linkedin(s: str) -> str:
    s = s.strip().lstrip("/")
    if not s.lower().startswith("http"):
        s = "https://www.linkedin.com/" + s
    # normalize double slashes, trailing punctuation
    return s.rstrip(").,;")

def _canon_github(s: str) -> str:
    s = s.strip().lstrip("/")
    s = s.replace("github/", "github.com/")
    if not s.lower().startswith("http"):
        s = "https://" + s
    return s.rstrip(").,;")

def detect_contacts(raw_text: str) -> Dict[str, List[str]]:
    emails = _dedupe_keep_order(EMAIL_RE.findall(raw_text))
    phones = _dedupe_keep_order(PHONE_RE.findall(raw_text))
    urls = _dedupe_keep_order(HTTP_URL_RE.findall(raw_text))

    # partials (convert to canon)
    ld_raw = LINKEDIN_PARTIAL_RE.findall(raw_text)
    gh_raw = GITHUB_PARTIAL_RE.findall(raw_text)

    linkedin = _dedupe_keep_order([_canon_linkedin(x) for x in ld_raw])
    github = _dedupe_keep_order([_canon_github(x) for x in gh_raw])

    # prefer explicit full URLs already in text
    linkedin_full = [u for u in urls if "linkedin.com/in/" in u.lower()]
    github_full = [u for u in urls if "github.com/" in u.lower()]

    # merge (full urls first)
    linkedin = _dedupe_keep_order(linkedin_full + linkedin)
    github = _dedupe_keep_order(github_full + github)

    # also keep other URLs (portfolio, notion, etc.)
    other_urls = [u for u in urls if ("linkedin.com/in/" not in u.lower() and "github.com/" not in u.lower())]

    return {
        "emails": emails,
        "phones": phones,
        "linkedin": linkedin,
        "github": github,
        "other_urls": _dedupe_keep_order(other_urls),
        "all_urls": _dedupe_keep_order(urls),
    }

def choose_primary(values: List[str]) -> str:
    return values[0] if values else None

def append_detected_block(text: str, detected: Dict[str, List[str]]) -> str:
    """Append a small machine-readable hints block the LLM can copy from."""
    block = [
        "\n\n=== DETECTED_CONTACTS ===",
        f"emails: {detected['emails']}",
        f"phones: {detected['phones']}",
        f"linkedin: {detected['linkedin']}",
        f"github: {detected['github']}",
        f"other_urls: {detected['other_urls']}",
        "=== END_DETECTED_CONTACTS ===\n",
    ]
    return text + "\n".join(block)

def postprocess_extracted(data: Dict[str, any], detected: Dict[str, List[str]]) -> Dict[str, any]:
    """Minimal, safe corrections using detected canonical links."""
    # prefer canonical email/phone if model missed or returned odd values
    if not data.get("email"):
        data["email"] = choose_primary(detected["emails"])
    if not data.get("phone"):
        data["phone"] = choose_primary(detected["phones"])

    # linkedin: ensure absolute https url
    llm_linkedin = data.get("linkedin_link")
    if not llm_linkedin or not str(llm_linkedin).lower().startswith("http"):
        data["linkedin_link"] = choose_primary(detected["linkedin"]) or llm_linkedin

    # portfolio_github_links: make sure list exists & contains canon github
    links = data.get("portfolio_github_links") or []
    # prepend detected github if missing
    for g in detected["github"]:
        if g not in links:
            links.insert(0, g)
    data["portfolio_github_links"] = _dedupe_keep_order(links)

    return data
