"""TC-ETL / TC-KPI: end-to-end checks on the real pipeline output."""
import sqlite3

import pandas as pd
import pytest

import etl
import kpis


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    db = tmp_path_factory.mktemp("dwh") / "test.db"
    po_raw, suppliers, budgets = etl.extract()
    po = etl.transform(po_raw)
    etl.load(po, suppliers, budgets, db_path=db)
    return po_raw, po, db


def test_tc_etl_001_duplicates_removed(warehouse):
    _, po, _ = warehouse
    assert po["po_id"].is_unique


def test_tc_etl_002_no_negative_amounts(warehouse):
    _, po, _ = warehouse
    assert (po["po_amount_mad"] > 0).all()


def test_tc_etl_003_no_missing_department(warehouse):
    _, po, _ = warehouse
    assert po["department"].notna().all()


def test_tc_etl_004_spend_reconciles_with_source(warehouse):
    """Total spend after cleaning = source spend, deduplicated, with signs fixed."""
    raw, po, _ = warehouse
    expected = raw.drop_duplicates("po_id")["po_amount_mad"].abs().sum()
    assert po["po_amount_mad"].sum() == pytest.approx(expected)


def test_tc_etl_005_row_count_in_warehouse(warehouse):
    _, po, db = warehouse
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM fact_purchase_order").fetchone()[0] == len(po)


def test_tc_etl_006_undelivered_orders_have_no_delay(warehouse):
    _, po, _ = warehouse
    assert po.loc[~po["is_delivered"], "delay_days"].isna().all()


def test_tc_kpi_001_sql_overview_matches_pandas(warehouse):
    _, po, db = warehouse
    overview = kpis.run_all(db)["overview"].iloc[0]
    assert overview["purchase_orders"] == len(po)
    assert overview["total_spend_m_mad"] == pytest.approx(po["po_amount_mad"].sum() / 1e6, abs=0.1)
    delivered = po[po["is_delivered"]]
    assert overview["on_time_rate_pct"] == pytest.approx(delivered["on_time"].mean() * 100, abs=0.1)


def test_tc_kpi_002_scores_between_0_and_100(warehouse):
    _, _, db = warehouse
    score = kpis.run_all(db)["supplier_scorecard"]["score"]
    assert score.between(0, 100).all()


def test_tc_kpi_003_all_queries_return_rows(warehouse):
    _, _, db = warehouse
    for name, df in kpis.run_all(db).items():
        assert isinstance(df, pd.DataFrame) and len(df) > 0, name


def test_tc_bi_001_powerbi_export_is_consistent(warehouse, tmp_path):
    """The Power BI files must carry the same spend as the warehouse, with valid keys."""
    from export_powerbi import export
    from quality import run_checks

    po_raw, po, _ = warehouse
    _, suppliers, budgets = etl.extract()
    export(po, suppliers, budgets, run_checks(po_raw, suppliers), out=tmp_path)

    fact = pd.read_csv(tmp_path / "fact_purchase_order.csv")
    dates = pd.read_csv(tmp_path / "dim_date.csv", parse_dates=["Date"])
    assert fact["po_amount_mad"].sum() == pytest.approx(po["po_amount_mad"].sum())
    assert fact["supplier_id"].isin(pd.read_csv(tmp_path / "dim_supplier.csv")["supplier_id"]).all()
    assert fact["department"].isin(pd.read_csv(tmp_path / "dim_department.csv")["department"]).all()
    assert pd.to_datetime(fact["order_date"]).isin(dates["Date"]).all()
    assert dates["Date"].is_unique
