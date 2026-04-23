from pathlib import Path

from enricher.db import init_db
from enricher.pipeline import EnrichmentPipeline

if __name__ == "__main__":
    init_db()
    run_id = EnrichmentPipeline().run(Path("data/input/NCEC_Update_April_2026.xlsx"))
    print(f"Completed run {run_id}")
