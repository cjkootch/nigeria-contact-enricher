from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .config import settings

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
OBFUSCATED_EMAIL_RE = re.compile(
    r"([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+)\s*([A-Za-z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+)\s*([A-Za-z]{2,})",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?:\+?234|0)[\d\s\-()]{7,}")
LINKEDIN_RE = re.compile(r"https?://(?:[\w.]+\.)?linkedin\.com/[^\s'\"]+")
WHATSAPP_RE = re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com)/[^\s'\"]+")
CONTACT_PATH_KEYWORDS = ["contact", "about", "team", "career", "support", "reach", "get-in-touch", "office", "locations"]
COMMON_CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/get-in-touch", "/reach-us", "/support"]
JUNK_EMAIL_DOMAINS = ("sentry.io", "wixpress.com", "example.com", "domain.com", "email.com")


def allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    robots = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots)
        rp.read()
        return rp.can_fetch(settings.user_agent, url)
    except Exception:
        return True


def fetch_page(url: str) -> str:
    time.sleep(settings.crawl_delay_seconds)
    if not allowed_by_robots(url):
        return ""
    resp = requests.get(url, timeout=settings.request_timeout_seconds, headers={"User-Agent": settings.user_agent})
    resp.raise_for_status()
    return resp.text


def extract_text_and_links(base_url: str, html: str) -> tuple[str, list[str], str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    text_parts = [soup.get_text(" ", strip=True)]
    for a in soup.select('a[href^="mailto:"]'):
        href = a.get("href", "").split("mailto:", 1)[-1].split("?")[0].strip()
        if href:
            text_parts.append(href)
    for a in soup.select('a[href^="tel:"]'):
        href = a.get("href", "").split("tel:", 1)[-1].strip()
        if href:
            text_parts.append(href)
    for tag in soup.find_all(attrs={"itemprop": ["email", "telephone"]}):
        text_parts.append(tag.get_text(" ", strip=True))
    text = " ".join(text_parts)
    links = []
    for a in soup.select("a[href]"):
        href = urljoin(base_url, a.get("href"))
        if urlparse(href).netloc == urlparse(base_url).netloc:
            links.append(href)
    return text, list(dict.fromkeys(links)), title


def crawl_candidate_pages(home_url: str, max_pages: int = 5) -> dict[str, str]:
    pages: dict[str, str] = {}
    try:
        home_html = fetch_page(home_url)
    except Exception:
        return pages
    home_text, links, _ = extract_text_and_links(home_url, home_html)
    pages[home_url] = home_text
    likely = [
        l
        for l in links
        if any(k in l.lower() for k in CONTACT_PATH_KEYWORDS)
    ]
    common_targets = [urljoin(home_url, p) for p in COMMON_CONTACT_PATHS]
    targets = list(dict.fromkeys(likely + common_targets))
    for url in targets[: max_pages - 1]:
        if url in pages:
            continue
        try:
            html = fetch_page(url)
            text, _, _ = extract_text_and_links(url, html)
            pages[url] = text
        except Exception:
            continue
    return pages


def extract_contacts(pages: dict[str, str]) -> dict:
    emails: list[tuple[str, str]] = []
    phones: list[tuple[str, str]] = []
    linkedin = None
    whatsapp = None
    address = None
    for url, text in pages.items():
        for em in EMAIL_RE.findall(text):
            em_low = em.lower()
            if not any(em_low.endswith(d) for d in JUNK_EMAIL_DOMAINS):
                emails.append((em_low, url))
        for user, dom, tld in OBFUSCATED_EMAIL_RE.findall(text):
            emails.append((f"{user}@{dom}.{tld}".lower(), url))
        for ph in PHONE_RE.findall(text):
            cleaned = re.sub(r"\s+", " ", ph).strip()
            phones.append((cleaned, url))
        if not linkedin:
            m = LINKEDIN_RE.search(text)
            if m:
                linkedin = m.group(0)
        if not whatsapp:
            m = WHATSAPP_RE.search(text)
            if m:
                whatsapp = m.group(0)
        if not address and any(k in text.lower() for k in ["street", "road", "avenue", "lagos", "abuja"]):
            address = text[:200]

    site_domain = ""
    if pages:
        site_domain = urlparse(next(iter(pages))).netloc.replace("www.", "").lower()
    on_domain = [(em, src) for em, src in emails if site_domain and em.endswith("@" + site_domain)]
    chosen_email_pair = on_domain[0] if on_domain else (emails[0] if emails else (None, None))

    return {
        "email": chosen_email_pair[0],
        "phone": phones[0][0] if phones else None,
        "address": address,
        "linkedin_url": linkedin,
        "whatsapp_url": whatsapp,
        "email_source_url": chosen_email_pair[1],
        "phone_source_url": phones[0][1] if phones else None,
    }
