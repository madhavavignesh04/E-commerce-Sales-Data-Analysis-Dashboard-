"""
STAGE 3 - RUN EVERY QUERY IN sql/analysis.sql
Run from the project root:  python python/run_queries.py

Prints each result and saves it as a CSV in outputs/.
These real results are the numbers you put in your README.
"""
import re
import sqlite3
from pathlib import Path
import pandas as pd

DB = Path("olist.db")
if not DB.exists():
    raise SystemExit("olist.db not found. Run python/build_db.py first.")

sql_text = Path("sql/analysis.sql").read_text(encoding="utf-8")
# Split on the "-- name: xxx" marker lines
parts = re.split(r"^-- name:\s*(\S+)\s*$", sql_text, flags=re.MULTILINE)
queries = list(zip(parts[1::2], parts[2::2]))

Path("outputs").mkdir(exist_ok=True)
con = sqlite3.connect(DB)
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

for name, body in queries:
    df = pd.read_sql_query(body.strip(), con)
    df.to_csv(Path("outputs") / f"{name}.csv", index=False)
    print("=" * 70)
    print(name)
    print("=" * 70)
    print(df.to_string(index=False) if len(df) <= 40 else df.head(40).to_string(index=False) + "\n...")
    print()
con.close()
print(f"Ran {len(queries)} queries. Results saved in outputs/")
