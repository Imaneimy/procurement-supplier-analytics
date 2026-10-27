"""Write the star schema as typed, clean CSVs for Power BI (see powerbi/POWERBI_GUIDE.md)."""
from pathlib import Path

import pandas as pd

POWERBI_DATA = Path(__file__).resolve().parents[1] / "powerbi" / "data"

FACT_COLUMNS = [
    "po_id", "supplier_id", "department", "category", "order_date", "promised_date",
    "delivered_date", "po_amount_mad", "invoice_amount_mad", "invoice_gap_mad",
    "is_delivered", "on_time", "delay_days", "lead_time_days", "invoice_match", "quality_issue",
]


def dim_date(start, end) -> pd.DataFrame:
    d = pd.DataFrame({"Date": pd.date_range(start, end, freq="D")})
    d["Year"] = d["Date"].dt.year
    d["Quarter"] = "Q" + d["Date"].dt.quarter.astype(str)
    d["YearQuarter"] = d["Date"].dt.to_period("Q").astype(str)
    d["MonthNumber"] = d["Date"].dt.month
    d["Month"] = d["Date"].dt.strftime("%b")
    d["YearMonth"] = d["Date"].dt.strftime("%Y-%m")
    return d


def export(po, suppliers, budgets, dq, out: Path = POWERBI_DATA) -> list:
    out.mkdir(parents=True, exist_ok=True)

    fact = po[FACT_COLUMNS].copy()
    # undelivered orders are neither on time nor late: leave blank so DAX ignores them
    fact["on_time"] = fact["on_time"].where(fact["is_delivered"])

    budget = budgets.copy()
    budget["quarter_start"] = pd.PeriodIndex(budget["quarter"], freq="Q").start_time

    tables = {
        "fact_purchase_order": fact,
        "fact_budget": budget,
        "dim_supplier": suppliers,
        "dim_department": pd.DataFrame({"department": sorted(fact["department"].unique())}),
        "dim_date": dim_date("2024-01-01", "2025-12-31"),
        "dq_results": dq,
    }
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    return list(tables)
