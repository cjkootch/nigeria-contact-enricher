from __future__ import annotations

import re
from urllib.parse import urlparse

from rapidfuzz import fuzz

from .config import SCORING_WEIGHTS
from .utils import normalize_company_name


def _contains_name(text: str, company: str) -> bool:
    return normalize_company_name(company) in normalize_company_name(text)


def _domain_similarity(url: str, company_name: str) -> float:
    domain = urlparse(url).netloc.lower().replace("www.", "")
    root = domain.split(".")[0].replace("-", " ")
    return fuzz.partial_ratio(normalize_company_name(company_name), root) / 100.0


def score_website(company_name: str, category: str | None, url: str, page_title: str, body_text: str, has_contact: bool, has_about: bool) -> dict:
    cnorm = normalize_company_name(company_name)
    tnorm = normalize_company_name(page_title)
    bnorm = normalize_company_name(body_text[:8000])
    exact_title = cnorm in tnorm and cnorm != ""
    exact_body = cnorm in bnorm and cnorm != ""
    fuzzy = fuzz.token_set_ratio(cnorm, tnorm + " " + bnorm) / 100.0
    domain = _domain_similarity(url, company_name)
    category_score = 0.0
    if category:
        keywords = [k for k in re.split(r"\W+", category.lower()) if len(k) > 3]
        if keywords:
            hits = sum(1 for k in keywords if k in body_text.lower() or k in page_title.lower())
            category_score = min(1.0, hits / max(1, len(keywords)))
    nigeria_signal = 1.0 if any(x in (url + page_title + body_text).lower() for x in ["nigeria", ".ng", "lagos", "abuja", "port harcourt"]) else 0.0
    brand_consistency = 1.0 if exact_title and exact_body else 0.5 if fuzzy > 0.6 else 0.0
    contact_about = 1.0 if has_contact or has_about else 0.0

    total = (
        (1.0 if exact_title else 0.0) * SCORING_WEIGHTS["title_exact"]
        + (1.0 if exact_body else 0.0) * SCORING_WEIGHTS["body_exact"]
        + fuzzy * SCORING_WEIGHTS["fuzzy_name"]
        + domain * SCORING_WEIGHTS["domain_similarity"]
        + category_score * SCORING_WEIGHTS["category_match"]
        + nigeria_signal * SCORING_WEIGHTS["nigeria_signal"]
        + contact_about * SCORING_WEIGHTS["contact_about_exists"]
        + brand_consistency * SCORING_WEIGHTS["branding_consistency"]
    )
    # Guard against unrelated sites passing on Nigeria/category signals alone:
    # require either a name-in-title match or meaningful domain overlap.
    if not exact_title and domain < 0.4 and fuzzy < 0.75:
        total = min(total, 45)
    status = "no_match"
    if total >= 80:
        status = "auto_accept"
    elif total >= 60:
        status = "review_needed"

    return {
        "website_match_score": round(total, 2),
        "exact_name_match": exact_title or exact_body,
        "fuzzy_name_score": round(fuzzy * 100, 2),
        "domain_similarity_score": round(domain * 100, 2),
        "category_match_score": round(category_score * 100, 2),
        "nigeria_signal_score": round(nigeria_signal * 100, 2),
        "status": status,
    }


def score_contacts(website_url: str, pages: dict[str, str], email: str | None, phone: str | None, address: str | None) -> float:
    score = 0.0
    if email:
        score += 30
        domain = urlparse(website_url).netloc.replace("www.", "")
        if email.lower().endswith("@" + domain):
            score += 20
    if phone:
        score += 25
        if any("contact" in key for key in pages.keys()):
            score += 10
    if address:
        score += 10
    if email and phone:
        repeated = sum(1 for text in pages.values() if email in text or phone in text)
        score += min(5, repeated)
    return min(100.0, score)
