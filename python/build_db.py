"""
STAGE 2 - LOAD THE CLEAN DATA INTO A SQLITE DATABASE
Run from the project root:  python python/build_db.py

SQLite is a database that lives in one file (olist.db). No server or install needed,
and the SQL (JOINs, CTEs, window functions) is the same you would write in MySQL.
"""
import sqlite3
from pathlib import Path
import pandas as pd

DB = Path("olist.db")
if DB.exists():
    DB.unlink()  # start fresh each time

TABLES = ["orders", "order_items", "payments", "reviews", "customers", "products"]

con = sqlite3.connect(DB)
for t in TABLES:
    path = Path("data/clean") / f"{t}.csv"
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run python/clean_data.py first.")
    df = pd.read_csv(path)
    df.to_sql(t, con, index=False)
    print(f"Loaded {t}: {len(df):,} rows")

# Indexes make JOINs fast
con.executescript("""
CREATE INDEX idx_orders_id        ON orders(order_id);
CREATE INDEX idx_orders_customer  ON orders(customer_id);
CREATE INDEX idx_items_order      ON order_items(order_id);
CREATE INDEX idx_items_product    ON order_items(product_id);
CREATE INDEX idx_pay_order        ON payments(order_id);
CREATE INDEX idx_rev_order        ON reviews(order_id);
CREATE INDEX idx_cust_id          ON customers(customer_id);
CREATE INDEX idx_prod_id          ON products(product_id);
""")
con.commit()
con.close()
print("\nDatabase created: olist.db")
