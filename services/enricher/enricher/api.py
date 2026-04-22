from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .db import Company, ExtractedContact, SessionLocal, WebsiteCandidate, init_db
from .pipeline import EnrichmentPipeline

app = FastAPI(title="Nigeria Contact Enricher")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/runs/default")
def run_default(limit: Optional[int] = None):
    pipeline = EnrichmentPipeline()
    run_id = pipeline.run(Path("data/input/NCEC_Update_April_2026.xlsx"), limit=limit)
    return {"run_id": run_id}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    target = Path("data/input") / file.filename
    contents = await file.read()
    target.write_bytes(contents)
    return {"saved_to": str(target)}


@app.get("/results")
def get_results(status: Optional[str] = None, missing_email: bool = False, missing_phone: bool = False):
    db = SessionLocal()
    query = db.query(Company, WebsiteCandidate, ExtractedContact).outerjoin(WebsiteCandidate, WebsiteCandidate.company_id == Company.id).outerjoin(ExtractedContact, ExtractedContact.company_id == Company.id)
    rows = []
    for c, w, e in query.all():
        row = {
            "company_name": c.company_name_raw,
            "service_category": c.service_category,
            "certificate_number": c.certificate_number,
            "found_website": w.candidate_url if w and w.accepted_boolean else (w.candidate_url if w else None),
            "email": e.email if e else None,
            "phone": e.phone if e else None,
            "website_match_score": w.website_match_score if w else 0,
            "contact_score": e.contact_score if e else 0,
            "final_confidence": e.final_confidence if e else 0,
            "status": c.processing_status,
            "notes": c.notes,
        }
        rows.append(row)
    db.close()
    df = pd.DataFrame(rows)
    if status:
        df = df[df["status"] == status]
    if missing_email:
        df = df[df["email"].isna()]
    if missing_phone:
        df = df[df["phone"].isna()]
    return df.fillna("").to_dict(orient="records")


@app.get("/export/csv")
def export_csv():
    return FileResponse("data/output/enriched_ncec_april_2026.csv", media_type="text/csv", filename="enriched_ncec_april_2026.csv")


@app.get("/export/xlsx")
def export_xlsx():
    return FileResponse(
        "data/output/enriched_ncec_april_2026.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="enriched_ncec_april_2026.xlsx",
    )
