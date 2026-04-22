from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .config import settings

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?234|0)[\d\s\-()]{7,}")
LINKEDIN_RE = re.compile(r"https?://(?:[\w.]+\.)?linkedin\.com/[^\s'\"]+")
WHATSAPP_RE = re.compile(r"https?://(?:wa\.me|api\.whatsapp\.com)/[^\s'\"]+")


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
    time.sleep(settings.request_delay_seconds)
    if not allowed_by_robots(url):
        return ""
    resp = requests.get(url, timeout=settings.request_timeout_seconds, headers={"User-Agent": settings.user_agent})
    resp.raise_for_status()
    return resp.text


def extract_text_and_links(base_url: str, html: str) -> tuple[str, list[str], str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)
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
        if any(k in l.lower() for k in ["contact", "about", "team", "career", "careers"])
    ]
    targets = [urljoin(home_url, "/contact"), urljoin(home_url, "/about")] + likely
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
            emails.append((em.lower(), url))
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

    email = emails[0][0] if emails else None
    phone = phones[0][0] if phones else None
    return {
        "email": email,
        "phone": phone,
        "address": address,
        "linkedin_url": linkedin,
        "whatsapp_url": whatsapp,
        "email_source_url": emails[0][1] if emails else None,
        "phone_source_url": phones[0][1] if phones else None,
    }
