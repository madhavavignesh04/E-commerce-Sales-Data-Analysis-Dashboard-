"""Data loading and KPI maths for the dashboard (kept separate so it is easy to test and explain)."""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "olist.db"

FACT_SQL = """
SELECT o.order_id,
       o.order_month,
       SUBSTR(o.order_month, 1, 4)              AS year,
       c.customer_state                         AS state,
       COALESCE(p.category_english, 'unknown')  AS category,
       i.price,
       i.freight_value,
       o.delivery_days,
       o.is_late,
       r.review_score
FROM orders o
JOIN customers c     ON c.customer_id = o.customer_id
JOIN order_items i   ON i.order_id = o.order_id
LEFT JOIN products p ON p.product_id = i.product_id
LEFT JOIN reviews r  ON r.order_id = o.order_id
WHERE o.order_status = 'delivered'
"""

PAY_SQL = "SELECT order_id, payment_type, payment_value FROM payments"


def load_data(db_path=DB_PATH):
    if not Path(db_path).exists():
        raise FileNotFoundError("olist.db not found. Run the cleaning and build_db scripts first.")
    con = sqlite3.connect(db_path)
    fact = pd.read_sql_query(FACT_SQL, con)
    pay = pd.read_sql_query(PAY_SQL, con)
    con.close()
    return fact, pay


def order_level(df):
    """One row per order (order-level facts such as review and delivery do not repeat per item)."""
    return df.drop_duplicates("order_id")


def kpis(df):
    orders = order_level(df)
    revenue = df["price"].sum()
    n_orders = orders["order_id"].nunique()
    late = orders["is_late"].dropna().astype(float)
    return {
        "revenue": revenue,
        "orders": n_orders,
        "aov": revenue / n_orders if n_orders else 0,
        "avg_review": orders["review_score"].mean(),
        "late_pct": 100 * late.mean() if len(late) else float("nan"),
        "avg_delivery_days": orders["delivery_days"].mean(),
    }


def monthly_revenue(df):
    return df.groupby("order_month", as_index=False)["price"].sum().rename(columns={"price": "revenue"})


def top_categories(df, n=10):
    out = df.groupby("category", as_index=False)["price"].sum().rename(columns={"price": "revenue"})
    return out.sort_values("revenue", ascending=False).head(n)


def revenue_by_state(df, n=10):
    out = df.groupby("state", as_index=False)["price"].sum().rename(columns={"price": "revenue"})
    return out.sort_values("revenue", ascending=False).head(n)


def review_by_delivery(df):
    o = order_level(df)
    o = o[o["is_late"].notna() & o["review_score"].notna()].copy()
    o["delivery"] = o["is_late"].astype(int).map({1: "Late", 0: "On time"})
    return o.groupby("delivery", as_index=False)["review_score"].mean().rename(columns={"review_score": "avg_review_score"})


def payment_mix(df, pay):
    ids = set(df["order_id"])
    p = pay[pay["order_id"].isin(ids)]
    return (p.groupby("payment_type")["order_id"].nunique().reset_index()
            .rename(columns={"order_id": "orders"}).sort_values("orders", ascending=False))
