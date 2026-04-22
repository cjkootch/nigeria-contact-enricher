# Nigeria Contact Enricher (MVP)

MVP web app + Python worker pipeline to enrich Nigerian company records from `NCEC_Update_April_2026.xlsx`.

## Workbook inspection summary

Inspected on **April 22, 2026**:
- File has 1 sheet: `Table 1`
- Header row detected at row 1
- 2,776 rows and 11 columns

Inferred mappings:
- `company_name` <- `Company Name` (`company_name`)
- `service_category` <- `Category of NCEC` (`category_of_ncec`)
- `certificate_number` <- `Certificate Number` (`certificate_number`)
- `status` <- `Status` (`status`)
- `approval_type` <- `New / Renewal` (`new_renewal`)
- `approval_date` <- `Date Approved` (`date_approved`)

## Project structure

```
/
  README.md
  .env.example
  /data
    /input
    /output
  /apps
    /web
  /services
    /enricher
  /packages
    /shared
```

## Features implemented

- Spreadsheet ingestion for all sheets
- Header row detection + snake_case normalization
- Source row/sheet preservation
- Search provider abstraction (`stub`, `duckduckgo`)
- Website scoring with configurable weights (`enricher/config.py`)
- Contact extraction (email/phone/address/LinkedIn/WhatsApp)
- Robots-aware static scraping + crawl limits
- SQLite/Postgres-compatible SQLAlchemy models
- FastAPI endpoints for upload/run/results/export
- Next.js UI for upload, run, filters, table, detail panel, exports
- CSV/XLSX output files in `data/output/`
- Unit tests for normalization, parser, scoring, extraction

## Quick start

### 1) Install dependencies

```bash
make install
```

### 2) Configure env

```bash
cp .env.example .env
```

### 3) Run API

```bash
make run-api
```

### 4) Run web UI

```bash
make run-web
```

Open http://localhost:3000.

### 5) Run subset pipeline from CLI

```bash
make run-subset
```

Default subset size in CLI helper is 25 rows; API supports `POST /runs/default?limit=...`.

## API endpoints

- `POST /upload` - upload an input spreadsheet to `data/input/`
- `POST /runs/default?limit=25` - run enrichment
- `GET /results` - list results with filters
- `GET /export/csv` - download CSV
- `GET /export/xlsx` - download XLSX

## Scoring

### Website match score (0-100)
Signals:
- exact name in title/body
- fuzzy name score
- domain similarity
- service category overlap
- Nigeria signals (`.ng`, `Nigeria`, location markers)
- contact/about page presence
- branding consistency

Thresholds:
- `>=80`: auto accept
- `60-79`: review needed
- `<60`: no match

### Contact score (0-100)
Rewards:
- email presence + official-domain email
- phone presence (extra for contact page)
- repeated details across pages
- address presence

### Final confidence
`final_confidence = 0.65 * website_match_score + 0.35 * contact_score`

## Search provider swap points

- Provider interface: `services/enricher/enricher/search.py`
- Current providers:
  - `StubSearchProvider`
  - `DuckDuckGoSearchProvider`
- Controlled by `SEARCH_PROVIDER` env var.

## Output files

- `data/output/enriched_ncec_april_2026.csv`
- `data/output/enriched_ncec_april_2026.xlsx`
- Example format: `data/output/example_enriched_output.csv`

## Notes / MVP limitations

- Playwright dependency is installed but static scraping is primary in this MVP.
- DuckDuckGo HTML response format can change; fallback provider available.
- UI currently triggers subset runs; remove limit for full file processing.
