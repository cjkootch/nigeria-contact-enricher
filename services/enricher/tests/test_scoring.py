from enricher.scoring import score_website


def test_score_website_positive_match():
    result = score_website(
        company_name="Acme Nigeria Limited",
        category="Procurement and Supplies",
        url="https://acme.com.ng",
        page_title="Acme Nigeria Limited",
        body_text="Acme Nigeria Limited provides procurement and supplies in Lagos, Nigeria.",
        has_contact=True,
        has_about=True,
    )
    assert result["website_match_score"] >= 80
