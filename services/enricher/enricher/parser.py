from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .utils import normalize_company_name, to_snake_case

logger = logging.getLogger(__name__)

COLUMN_ALIASES = {
    "company_name": ["company_name", "company name"],
    "service_category": ["category_of_ncec", "service_category", "category"],
    "certificate_number": ["certificate_number", "certificate no", "certificate"],
    "status": ["status"],
    "approval_type": ["new_renewal", "new / renewal", "approval_type"],
    "approval_date": ["date_approved", "approval_date"],
}


def detect_header_row(df: pd.DataFrame, max_probe_rows: int = 20) -> int:
    best_idx = 0
    best_score = -1
    for idx in range(min(max_probe_rows, len(df))):
        row = df.iloc[idx].astype(str).str.lower().tolist()
        score = sum(1 for cell in row for token in ["company", "certificate", "status", "date"] if token in cell)
        if score > best_score:
            best_idx = idx
            best_score = score
    return best_idx


def infer_mapping(columns: Iterable[str]) -> dict[str, str | None]:
    mapped: dict[str, str | None] = {}
    normalized = {to_snake_case(c): c for c in columns}
    for target, aliases in COLUMN_ALIASES.items():
        mapped[target] = None
        for alias in aliases:
            if alias in normalized:
                mapped[target] = normalized[alias]
                break
    return mapped


def parse_workbook(path: Path) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    mappings: list[dict] = []
    xls = pd.ExcelFile(path)
    for sheet_name in xls.sheet_names:
        raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
        header_row = detect_header_row(raw)
        frame = pd.read_excel(path, sheet_name=sheet_name, header=header_row)
        frame.columns = [to_snake_case(c) for c in frame.columns]
        mapping = infer_mapping(frame.columns)
        logger.info("Inferred mapping for %s: %s", sheet_name, mapping)
        mappings.append({"sheet": sheet_name, "header_row": header_row + 1, "mapping": mapping})
        for idx, rec in enumerate(frame.to_dict(orient="records")):
            record = dict(rec)
            record["_source_sheet"] = sheet_name
            record["_source_row_number"] = int(idx) + header_row + 2
            company = str(record.get(mapping.get("company_name") or "company_name", "")).strip()
            record["company_name_normalized"] = normalize_company_name(company)
            rows.append(record)
    return rows, mappings
