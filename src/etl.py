"""Extract raw CSVs, check quality, clean, and load into a SQLite warehouse."""
import sqlite3
from pathlib import Path

import pandas as pd

from quality import run_checks

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "procurement.db"


def extract():
    po = pd.read_csv(RAW / "purchase_orders.csv",
                     parse_dates=["order_date", "promised_date", "delivered_date"])
    suppliers = pd.read_csv(RAW / "suppliers.csv")
    budgets = pd.read_csv(RAW / "budgets.csv")
    return po, suppliers, budgets


def transform(po: pd.DataFrame) -> pd.DataFrame:
    po = po.drop_duplicates(subset="po_id", keep="first").copy()
    po["po_amount_mad"] = po["po_amount_mad"].abs()        # sign errors confirmed as keying mistakes
    po["department"] = po["department"].fillna("Unassigned")

    po["is_delivered"] = po["delivered_date"].notna()
    po["delay_days"] = (po["delivered_date"] - po["promised_date"]).dt.days
    po["on_time"] = po["delay_days"] <= 0
    po["lead_time_days"] = (po["delivered_date"] - po["order_date"]).dt.days
    po["invoice_gap_mad"] = (po["invoice_amount_mad"] - po["po_amount_mad"]).round(2)
    po["invoice_match"] = po["invoice_gap_mad"].abs() <= po["po_amount_mad"] * 0.01
    po["month"] = po["order_date"].dt.to_period("M").astype(str)
    po["quarter"] = po["order_date"].dt.to_period("Q").astype(str)
    return po


def load(po, suppliers, budgets, db_path: Path = DB_PATH):
    with sqlite3.connect(db_path) as con:
        po.assign(**{c: po[c].dt.strftime("%Y-%m-%d")
                     for c in ["order_date", "promised_date", "delivered_date"]}) \
          .to_sql("fact_purchase_order", con, if_exists="replace", index=False)
        suppliers.to_sql("dim_supplier", con, if_exists="replace", index=False)
        budgets.to_sql("fact_budget", con, if_exists="replace", index=False)


def run():
    po_raw, suppliers, budgets = extract()
    dq = run_checks(po_raw, suppliers)
    po = transform(po_raw)
    load(po, suppliers, budgets)
    return po, suppliers, budgets, dq
