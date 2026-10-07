"""
STAGE 1 - CLEAN THE RAW OLIST DATA
Run from the project root:  python python/clean_data.py

What this script does (in plain words):
1. Reads the 7 raw CSV files we need from data/raw/ (it never edits them).
2. Looks for data-quality problems and COUNTS each one.
3. Fixes them in code, so anyone can repeat the cleaning.
4. Saves clean CSVs to data/clean/ and a data-quality report you can paste into your README.
"""
from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
CLEAN = Path("data/clean")
CLEAN.mkdir(parents=True, exist_ok=True)

report = []  # every line we log is also saved to the report file


def log(msg=""):
    print(msg)
    report.append(msg)


def load(name):
    path = RAW / name
    if not path.exists():
        raise SystemExit(f"Missing file: {path}. Copy the Olist CSV files into data/raw/ first.")
    return pd.read_csv(path)


orders = load("olist_orders_dataset.csv")
items = load("olist_order_items_dataset.csv")
payments = load("olist_order_payments_dataset.csv")
reviews = load("olist_order_reviews_dataset.csv")
customers = load("olist_customers_dataset.csv")
products = load("olist_products_dataset.csv")
translation = load("product_category_name_translation.csv")

log("# Data Quality Report")
log()
log("## Raw row counts")
for name, df in [("orders", orders), ("order_items", items), ("payments", payments),
                 ("reviews", reviews), ("customers", customers), ("products", products),
                 ("category_translation", translation)]:
    log(f"- {name}: {len(df):,} rows")

# ---------------------------------------------------------------- ORDERS
log()
log("## Orders")
date_cols = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
             "order_delivered_customer_date", "order_estimated_delivery_date"]
for c in date_cols:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")

dup_orders = int(orders.duplicated("order_id").sum())
log(f"- Duplicate order_id rows: {dup_orders:,}")
orders = orders.drop_duplicates("order_id")

log("- Orders by status:")
for status, n in orders["order_status"].value_counts().items():
    log(f"    - {status}: {n:,}")

for c in date_cols:
    log(f"- Missing {c}: {int(orders[c].isna().sum()):,}")

delivered_no_date = int(((orders["order_status"] == "delivered") &
                         orders["order_delivered_customer_date"].isna()).sum())
log(f"- Orders marked 'delivered' but with no delivery date: {delivered_no_date:,}")

# Derived columns we will use in SQL and the dashboard
orders["order_month"] = orders["order_purchase_timestamp"].dt.strftime("%Y-%m")
orders["delivery_days"] = ((orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"])
                           .dt.total_seconds() / 86400).round(1)
orders["delay_days"] = ((orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"])
                        .dt.total_seconds() / 86400).round(1)

bad_dates = int((orders["delivery_days"] < 0).sum())
log(f"- Orders delivered BEFORE purchase date (impossible, set to missing): {bad_dates:,}")
orders.loc[orders["delivery_days"] < 0, ["delivery_days", "delay_days"]] = float("nan")

orders["is_late"] = pd.Series(pd.NA, index=orders.index, dtype="Int64")
has_delay = orders["delay_days"].notna()
orders.loc[has_delay, "is_late"] = (orders.loc[has_delay, "delay_days"] > 0).astype(int)

orders_clean = orders[["order_id", "customer_id", "order_status", "order_purchase_timestamp",
                       "order_month", "order_delivered_customer_date", "order_estimated_delivery_date",
                       "delivery_days", "delay_days", "is_late"]]

# ----------------------------------------------------------------- ITEMS
log()
log("## Order items")
dup_items = int(items.duplicated(["order_id", "order_item_id"]).sum())
log(f"- Duplicate (order_id, order_item_id) rows: {dup_items:,}")
items = items.drop_duplicates(["order_id", "order_item_id"])
bad_price = int((items["price"] <= 0).sum())
log(f"- Items with price <= 0: {bad_price:,}")
items = items[items["price"] > 0]
log(f"- Items whose order_id is not in orders: {int((~items['order_id'].isin(orders['order_id'])).sum()):,}")
items_clean = items[["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"]]

# -------------------------------------------------------------- PAYMENTS
log()
log("## Payments")
log(f"- Duplicate rows: {int(payments.duplicated().sum()):,}")
payments = payments.drop_duplicates()
log(f"- Payments with value 0: {int((payments['payment_value'] == 0).sum()):,}")
log(f"- Payments with type 'not_defined': {int((payments['payment_type'] == 'not_defined').sum()):,}")
payments_clean = payments[["order_id", "payment_sequential", "payment_type",
                           "payment_installments", "payment_value"]]

# --------------------------------------------------------------- REVIEWS
log()
log("## Reviews")
reviews["review_answer_timestamp"] = pd.to_datetime(reviews["review_answer_timestamp"], errors="coerce")
reviews["review_creation_date"] = pd.to_datetime(reviews["review_creation_date"], errors="coerce")
multi = reviews.groupby("order_id").size()
log(f"- Orders with more than one review: {int((multi > 1).sum()):,} (we keep only the latest review per order)")
log(f"- Missing review comment text: {int(reviews['review_comment_message'].isna().sum()):,} "
    f"of {len(reviews):,} (normal - many customers only give a star rating)")
reviews = (reviews.sort_values("review_answer_timestamp")
           .drop_duplicates("order_id", keep="last"))
reviews_clean = reviews[["order_id", "review_score", "review_creation_date"]]

# ------------------------------------------------------------- CUSTOMERS
log()
log("## Customers")
log(f"- Duplicate customer_id rows: {int(customers.duplicated('customer_id').sum()):,}")
customers = customers.drop_duplicates("customer_id")
log(f"- customer_id values: {customers['customer_id'].nunique():,}  |  "
    f"real unique people (customer_unique_id): {customers['customer_unique_id'].nunique():,}")
customers["customer_state"] = customers["customer_state"].str.strip().str.upper()
customers_clean = customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]]

# -------------------------------------------------------------- PRODUCTS
log()
log("## Products")
log(f"- Duplicate product_id rows: {int(products.duplicated('product_id').sum()):,}")
products = products.drop_duplicates("product_id")
log(f"- Products with missing category: {int(products['product_category_name'].isna().sum()):,}")
products = products.merge(translation, on="product_category_name", how="left")
no_translation = int((products["product_category_name"].notna() &
                      products["product_category_name_english"].isna()).sum())
log(f"- Products whose category has no English translation (Portuguese name kept): {no_translation:,}")
products["category_english"] = (products["product_category_name_english"]
                                .fillna(products["product_category_name"])
                                .fillna("unknown"))
products_clean = products[["product_id", "category_english"]]

# ------------------------------------------------------ CROSS-TABLE CHECKS
log()
log("## Cross-table checks")
no_items = ~orders["order_id"].isin(items["order_id"])
log(f"- Orders with no items: {int(no_items.sum()):,}")
log(f"- Orders with no payment record: {int((~orders['order_id'].isin(payments['order_id'])).sum()):,}")
log(f"- Orders with no review: {int((~orders['order_id'].isin(reviews['order_id'])).sum()):,}")

# ----------------------------------------------------------------- SAVE
log()
log("## Clean row counts (saved to data/clean/)")
for name, df in [("orders", orders_clean), ("order_items", items_clean), ("payments", payments_clean),
                 ("reviews", reviews_clean), ("customers", customers_clean), ("products", products_clean)]:
    df.to_csv(CLEAN / f"{name}.csv", index=False)
    log(f"- {name}: {len(df):,} rows")

first = orders["order_purchase_timestamp"].min()
last = orders["order_purchase_timestamp"].max()
log()
log(f"Order date range: {first} to {last}")

(CLEAN / "data_quality_report.md").write_text("\n".join(report), encoding="utf-8")
print("\nDone. Report saved to data/clean/data_quality_report.md")
