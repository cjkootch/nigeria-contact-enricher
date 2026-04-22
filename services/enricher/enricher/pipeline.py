from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from .db import Company, Evidence, ExtractedContact, ProcessingRun, SessionLocal, WebsiteCandidate
from .parser import parse_workbook
from .scoring import score_contacts, score_website
from .scraper import crawl_candidate_pages, extract_contacts
from .search import get_search_provider


class EnrichmentPipeline:
    def __init__(self) -> None:
        self.search = get_search_provider()

    def run(self, input_file: Path, limit: int | None = None) -> int:
        db = SessionLocal()
        run = ProcessingRun(
            input_filename=input_file.name,
            started_at=datetime.utcnow(),
            settings_json=json.dumps({"limit": limit}),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        rows, _mappings = parse_workbook(input_file)
        if limit:
            rows = rows[:limit]
        run.total_rows = len(rows)
        db.commit()

        output_rows = []
        for row in rows:
            try:
                company_name = str(row.get("company_name") or row.get("company_name_raw") or "").strip()
                service_category = str(row.get("category_of_ncec") or row.get("service_category") or "")
                company = Company(
                    source_file=input_file.name,
                    source_sheet=row.get("_source_sheet", "Sheet1"),
                    source_row_number=row.get("_source_row_number", 0),
                    company_name_raw=company_name,
                    company_name_normalized=row.get("company_name_normalized", ""),
                    service_category=service_category,
                    certificate_number=str(row.get("certificate_number") or ""),
                    status=str(row.get("status") or ""),
                    approval_type=str(row.get("new_renewal") or row.get("approval_type") or ""),
                    approval_date=str(row.get("date_approved") or row.get("approval_date") or ""),
                    processing_status="processing",
                )
                db.add(company)
                db.commit()
                db.refresh(company)

                queries = [
                    f"{company_name}",
                    f"{company_name} Nigeria",
                    f"{company_name} {service_category}".strip(),
                    f"{company_name} oil and gas Nigeria",
                ]
                best = None
                best_status = "no_match"
                for q in queries:
                    results = self.search.search(q, limit=3)
                    for i, result in enumerate(results, start=1):
                        pages = crawl_candidate_pages(result.url, max_pages=3)
                        body = "\n".join(pages.values())
                        score = score_website(
                            company_name=company_name,
                            category=service_category,
                            url=result.url,
                            page_title=result.title,
                            body_text=body,
                            has_contact=any("contact" in u.lower() for u in pages),
                            has_about=any("about" in u.lower() for u in pages),
                        )
                        candidate = WebsiteCandidate(
                            company_id=company.id,
                            candidate_url=result.url,
                            root_domain=urlparse(result.url).netloc,
                            page_title=result.title,
                            search_query=q,
                            candidate_rank=i,
                            exact_name_match=score["exact_name_match"],
                            fuzzy_name_score=score["fuzzy_name_score"],
                            domain_similarity_score=score["domain_similarity_score"],
                            category_match_score=score["category_match_score"],
                            nigeria_signal_score=score["nigeria_signal_score"],
                            website_match_score=score["website_match_score"],
                            accepted_boolean=False,
                        )
                        db.add(candidate)
                        db.flush()
                        if best is None or candidate.website_match_score > best.website_match_score:
                            best = candidate
                            best_status = score["status"]
                if best:
                    best.accepted_boolean = best.website_match_score >= 80
                    pages = crawl_candidate_pages(best.candidate_url)
                    contacts = extract_contacts(pages)
                    contact_score = score_contacts(best.candidate_url, pages, contacts.get("email"), contacts.get("phone"), contacts.get("address"))
                    final_confidence = round(0.65 * best.website_match_score + 0.35 * contact_score, 2)
                    extracted = ExtractedContact(
                        company_id=company.id,
                        accepted_website_url=best.candidate_url,
                        contact_page_url=next((u for u in pages if "contact" in u.lower()), best.candidate_url),
                        email=contacts.get("email"),
                        phone=contacts.get("phone"),
                        address=contacts.get("address"),
                        linkedin_url=contacts.get("linkedin_url"),
                        email_source_url=contacts.get("email_source_url"),
                        phone_source_url=contacts.get("phone_source_url"),
                        contact_score=contact_score,
                        final_confidence=final_confidence,
                        review_flag=60 <= best.website_match_score < 80,
                    )
                    db.add(extracted)
                    if contacts.get("email"):
                        db.add(Evidence(company_id=company.id, field_name="email", field_value=contacts["email"], source_url=contacts.get("email_source_url"), source_kind="scrape", confidence=contact_score / 100))
                    if contacts.get("phone"):
                        db.add(Evidence(company_id=company.id, field_name="phone", field_value=contacts["phone"], source_url=contacts.get("phone_source_url"), source_kind="scrape", confidence=contact_score / 100))
                    company.processing_status = best_status
                else:
                    company.processing_status = "no_match"

                run.completed_rows += 1
                db.commit()

                output_rows.append(
                    {
                        "company_name": company.company_name_raw,
                        "service_category": company.service_category,
                        "certificate_number": company.certificate_number,
                        "found_website": best.candidate_url if best else None,
                        "email": contacts.get("email") if best else None,
                        "phone": contacts.get("phone") if best else None,
                        "website_match_score": best.website_match_score if best else 0,
                        "contact_score": contact_score if best else 0,
                        "final_confidence": final_confidence if best else 0,
                        "status": company.processing_status,
                        "notes": company.notes,
                    }
                )
            except Exception as exc:
                run.failed_rows += 1
                db.commit()
                output_rows.append({"company_name": row.get("company_name"), "status": "failed", "notes": str(exc)})

        run.completed_at = datetime.utcnow()
        db.commit()
        run_id = run.id

        out_csv = Path("data/output/enriched_ncec_april_2026.csv")
        out_xlsx = Path("data/output/enriched_ncec_april_2026.xlsx")
        pd.DataFrame(output_rows).to_csv(out_csv, index=False)
        pd.DataFrame(output_rows).to_excel(out_xlsx, index=False)
        db.close()
        return run_id
