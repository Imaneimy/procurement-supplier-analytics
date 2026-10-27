"""Entry point: raw CSVs → quality checks → SQLite warehouse → SQL KPIs → Power BI export."""
import time

import etl
import kpis
from export_powerbi import POWERBI_DATA, export


def main():
    start = time.perf_counter()
    po, suppliers, budgets, dq = etl.run()
    print("== Data quality ==")
    print(dq.to_string(index=False))

    # SQL KPIs act as the reference values the Power BI measures must match
    results = kpis.run_all()
    print("\n== Reference KPIs (SQL) ==")
    print(results["overview"].T.to_string(header=False))
    print("\n== Lowest supplier scores ==")
    print(results["supplier_scorecard"].nsmallest(5, "score").to_string(index=False))

    tables = export(po, suppliers, budgets, dq)
    print(f"\nPower BI tables written to {POWERBI_DATA}: {', '.join(tables)}")
    print(f"Done in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
