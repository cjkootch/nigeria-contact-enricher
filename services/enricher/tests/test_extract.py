from enricher.scraper import extract_contacts


def test_extract_email_and_phone():
    pages = {
        "https://acme-nigeria.com": "Email us info@acme-nigeria.com Call +234 800 123 4567",
        "https://acme-nigeria.com/contact": "contact@acme-nigeria.com 08031234567",
    }
    result = extract_contacts(pages)
    assert result["email"] == "info@acme-nigeria.com"
    assert result["phone"] is not None


def test_extract_obfuscated_email():
    pages = {"https://acme.ng": "Reach us at sales [at] acme [dot] ng for quotes"}
    result = extract_contacts(pages)
    assert result["email"] == "sales@acme.ng"


def test_prefers_on_domain_email():
    pages = {
        "https://acme.com.ng": "owner@gmail.com is our backup. info@acme.com.ng is preferred.",
    }
    result = extract_contacts(pages)
    assert result["email"] == "info@acme.com.ng"
