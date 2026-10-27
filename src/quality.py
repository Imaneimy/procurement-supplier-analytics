"""
Data quality checks run before any KPI is computed.
Each check has an ID so results can be tracked like test cases (XRAY-style).
"""
import pandas as pd


def run_checks(po: pd.DataFrame, suppliers: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("DQ-001", "PO id is unique", po["po_id"].duplicated(keep="first")),
        ("DQ-002", "PO amount is positive", po["po_amount_mad"] <= 0),
        ("DQ-003", "Department is filled", po["department"].isna()),
        ("DQ-004", "Supplier exists in master data", ~po["supplier_id"].isin(suppliers["supplier_id"])),
        ("DQ-005", "Promised date is after order date", po["promised_date"] < po["order_date"]),
        ("DQ-006", "Invoice matches PO amount (±1%)",
         (po["invoice_amount_mad"] - po["po_amount_mad"].abs()).abs() > po["po_amount_mad"].abs() * 0.01),
    ]
    rows = []
    for check_id, rule, failed in checks:
        n = int(failed.sum())
        rows.append({
            "check_id": check_id,
            "rule": rule,
            "rows_failed": n,
            "pct_failed": round(n / len(po) * 100, 2),
            # DQ-006 is a business finding to report, not a reason to reject the row
            "status": "PASS" if n == 0 else ("WARN" if check_id == "DQ-006" else "FAIL"),
        })
    return pd.DataFrame(rows)
