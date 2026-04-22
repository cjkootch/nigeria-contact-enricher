from enricher.scraper import extract_contacts


def test_extract_email_and_phone():
    pages = {
        "https://example.com": "Email us info@example.com Call +234 800 123 4567",
        "https://example.com/contact": "contact@example.com 08031234567",
    }
    result = extract_contacts(pages)
    assert result["email"] == "info@example.com"
    assert result["phone"] is not None
