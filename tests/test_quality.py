"""TC-DQ: the quality checks must catch each kind of defect, and only that."""
import pandas as pd
import pytest

from quality import run_checks


@pytest.fixture
def suppliers():
    return pd.DataFrame({"supplier_id": ["SUP001", "SUP002"]})


@pytest.fixture
def clean_po():
    return pd.DataFrame({
        "po_id": ["PO1", "PO2", "PO3"],
        "supplier_id": ["SUP001", "SUP002", "SUP001"],
        "department": ["IT", "HR", "Network"],
        "order_date": pd.to_datetime(["2024-01-01"] * 3),
        "promised_date": pd.to_datetime(["2024-01-20"] * 3),
        "po_amount_mad": [1000.0, 2000.0, 3000.0],
        "invoice_amount_mad": [1000.0, 2000.0, 3000.0],
    })


def status(dq, check_id):
    return dq.set_index("check_id").loc[check_id, "status"]


def test_tc_dq_000_clean_data_passes_everything(clean_po, suppliers):
    assert (run_checks(clean_po, suppliers)["status"] == "PASS").all()


@pytest.mark.parametrize("check_id, column, value", [
    ("DQ-001", "po_id", "PO1"),
    ("DQ-002", "po_amount_mad", -500.0),
    ("DQ-003", "department", None),
    ("DQ-004", "supplier_id", "SUP999"),
    ("DQ-005", "promised_date", pd.Timestamp("2023-12-01")),
])
def test_tc_dq_001_to_005_each_defect_is_caught(clean_po, suppliers, check_id, column, value):
    clean_po.loc[2, column] = value
    dq = run_checks(clean_po, suppliers)
    assert status(dq, check_id) == "FAIL"
    assert dq.set_index("check_id").loc[check_id, "rows_failed"] == 1


def test_tc_dq_006_invoice_mismatch_is_a_warning(clean_po, suppliers):
    clean_po.loc[0, "invoice_amount_mad"] = 1100.0
    assert status(run_checks(clean_po, suppliers), "DQ-006") == "WARN"


def test_tc_dq_007_invoice_within_tolerance_passes(clean_po, suppliers):
    clean_po.loc[0, "invoice_amount_mad"] = 1005.0  # +0.5%
    assert status(run_checks(clean_po, suppliers), "DQ-006") == "PASS"
