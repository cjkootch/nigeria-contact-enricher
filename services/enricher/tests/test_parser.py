import pandas as pd

from enricher.parser import detect_header_row, infer_mapping


def test_detect_header_row():
    df = pd.DataFrame([["x", "y"], ["Company Name", "Status"], ["ACME", "APPROVED"]])
    assert detect_header_row(df) == 1


def test_infer_mapping():
    mapping = infer_mapping(["company_name", "category_of_ncec", "certificate_number", "status", "date_approved"])
    assert mapping["company_name"] == "company_name"
    assert mapping["approval_date"] == "date_approved"
