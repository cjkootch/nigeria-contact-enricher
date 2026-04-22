from enricher.utils import normalize_company_name, to_snake_case


def test_to_snake_case():
    assert to_snake_case("Company Name") == "company_name"


def test_normalize_company_name():
    assert normalize_company_name("ACME SERVICES LIMITED") == "acme"
