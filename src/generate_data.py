"""
Generate a realistic, fully synthetic procurement dataset.

No real company data is used. The structure (suppliers, purchase orders, invoices,
budgets) mirrors what a telecom procurement team works with day to day, and a few
real-world problems are injected on purpose so the quality checks have something to find.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
rng = np.random.default_rng(42)

CATEGORIES = {
    # category: (typical PO amount in MAD, share of POs)
    "Network Equipment": (420_000, 0.14),
    "IT Hardware": (85_000, 0.20),
    "Software Licences": (150_000, 0.10),
    "Telecom Infrastructure": (650_000, 0.08),
    "Facility Services": (35_000, 0.22),
    "Marketing & Events": (60_000, 0.12),
    "Consulting": (180_000, 0.14),
}
DEPARTMENTS = ["Network", "IT", "Marketing", "Finance", "HR", "Customer Care", "General Services"]
# which departments usually buy each category
BUYERS = {
    "Network Equipment": ["Network"],
    "IT Hardware": ["IT", "IT", "Customer Care", "Finance", "HR"],
    "Software Licences": ["IT", "IT", "Finance", "Marketing", "Customer Care"],
    "Telecom Infrastructure": ["Network"],
    "Facility Services": ["General Services", "General Services", "HR", "Customer Care"],
    "Marketing & Events": ["Marketing"],
    "Consulting": ["Finance", "IT", "Network", "HR", "Marketing"],
}
CITIES = ["Casablanca", "Rabat", "Tangier", "Marrakech", "Fes", "Agadir", "Paris", "Madrid"]


def suppliers(n=45):
    cats = list(CATEGORIES)
    rows = []
    for i in range(1, n + 1):
        rows.append({
            "supplier_id": f"SUP{i:03d}",
            "supplier_name": f"Supplier {i:03d}",
            "category": cats[(i - 1) % len(cats)],
            "city": rng.choice(CITIES, p=[.35, .2, .1, .08, .07, .05, .1, .05]),
            "has_framework_contract": bool(rng.random() < 0.7),
            # hidden "true" reliability, drives delays and quality issues
            "_reliability": rng.beta(6, 2),
        })
    return pd.DataFrame(rows)


def purchase_orders(sup, n=6000):
    cats = list(CATEGORIES)
    probs = np.array([CATEGORIES[c][1] for c in cats])
    cat = rng.choice(cats, size=n, p=probs / probs.sum())
    order_date = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 547, n), "D")

    rows = []
    for i in range(n):
        pool = sup[sup["category"] == cat[i]]
        # a few big suppliers take most of the business (Pareto)
        w = np.linspace(3, 0.3, len(pool))
        s = pool.iloc[rng.choice(len(pool), p=w / w.sum())]
        amount = round(float(rng.lognormal(np.log(CATEGORIES[cat[i]][0]), 0.6)), 2)
        lead = int(rng.integers(10, 45))
        promised = order_date[i] + pd.Timedelta(days=lead)
        delay = int(rng.poisson((1 - s["_reliability"]) * 25)) if rng.random() > s["_reliability"] else 0
        delivered = promised + pd.Timedelta(days=delay - int(rng.integers(0, 4)))
        invoice = amount if rng.random() < 0.9 else round(amount * rng.uniform(1.01, 1.15), 2)
        rows.append({
            "po_id": f"PO{100000 + i}",
            "supplier_id": s["supplier_id"],
            "category": cat[i],
            "department": rng.choice(BUYERS[cat[i]]),
            "order_date": order_date[i].date(),
            "promised_date": promised.date(),
            "delivered_date": delivered.date(),
            "po_amount_mad": amount,
            "invoice_amount_mad": invoice,
            "quality_issue": bool(rng.random() < (1 - s["_reliability"]) * 0.3),
        })
    po = pd.DataFrame(rows)

    # Real-world mess, on purpose
    open_idx = po.sort_values("order_date").tail(150).index        # not delivered yet
    po.loc[open_idx, "delivered_date"] = None
    po.loc[po.sample(25, random_state=1).index, "department"] = None  # missing department
    po.loc[po.sample(12, random_state=2).index, "po_amount_mad"] *= -1  # sign errors
    dupes = po.sample(30, random_state=3)                             # double-keyed POs
    return pd.concat([po, dupes], ignore_index=True)


def budgets(po):
    # budgets set around what each department really spends, so some end up over, some under
    yearly = po.groupby("department")["po_amount_mad"].sum() / 1.5
    rows = []
    for dept in DEPARTMENTS:
        base = yearly[dept] * rng.uniform(0.85, 1.2)
        for q in pd.period_range("2024Q1", "2025Q2", freq="Q"):
            rows.append({"department": dept, "quarter": str(q),
                         "budget_mad": round(base / 4 * rng.uniform(0.9, 1.1), 2)})
    return pd.DataFrame(rows)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    sup = suppliers()
    sup.drop(columns="_reliability").to_csv(RAW / "suppliers.csv", index=False)
    po = purchase_orders(sup)
    po.to_csv(RAW / "purchase_orders.csv", index=False)
    budgets(po.dropna(subset=["department"]).drop_duplicates("po_id").assign(
        po_amount_mad=lambda d: d["po_amount_mad"].abs())).to_csv(RAW / "budgets.csv", index=False)
    print(f"Synthetic data written to {RAW}")


if __name__ == "__main__":
    main()
