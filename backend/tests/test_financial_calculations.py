import pytest
from decimal import Decimal
import datetime
from backend.app.calculations.financial import (
    calculate_dti,
    calculate_foir,
    calculate_disposable_income,
    calculate_reducing_emi,
    generate_amortization_schedule,
    verify_schedule_reconciliation,
    quantize_currency
)

def test_dti_calculation():
    # Existing debt: 15,000, Gross income: 60,000 -> DTI = 25.00%
    dti = calculate_dti(15000, 60000)
    assert dti == Decimal("25.00")

    # Zero gross income guard
    dti_zero = calculate_dti(5000, 0)
    assert dti_zero == Decimal("100.00")


def test_foir_calculation():
    # Debt: 10,000, Proposed EMI: 15,000, Net income: 50,000 -> (25,000 / 50,000) * 100 = 50.00%
    foir = calculate_foir(10000, 15000, 50000)
    assert foir == Decimal("50.00")

    # Zero net income guard
    foir_zero = calculate_foir(10000, 5000, 0)
    assert foir_zero == Decimal("100.00")


def test_disposable_income():
    # Net: 70,000, Debt: 15,000, Proposed EMI: 20,000 -> 35,000
    disp = calculate_disposable_income(70000, 15000, 20000)
    assert disp == Decimal("35000.00")


def test_reducing_emi_calculation():
    # P = 500,000, rate = 12% p.a., n = 12 months
    # Formula check: monthly rate = 1%, (1.01)^12 = 1.126825...
    # EMI should be approx 44,424.39
    emi = calculate_reducing_emi(500000, 12.0, 12)
    assert emi == Decimal("44424.39")


def test_zero_interest_loan_emi():
    # P = 120,000, rate = 0%, n = 12 months -> EMI = 10,000.00
    emi = calculate_reducing_emi(120000, 0.0, 12)
    assert emi == Decimal("10000.00")


def test_amortization_schedule_reconciliation():
    principal = Decimal("1000000.00")
    rate = Decimal("9.50")
    term = 36
    start_date = datetime.date(2026, 1, 15)

    schedule = generate_amortization_schedule(
        application_id="LOAN-2026-000001",
        principal=principal,
        annual_interest_rate=rate,
        term_months=term,
        disbursement_date=start_date
    )

    assert len(schedule) == term
    assert schedule[0]["installment_number"] == 1
    assert schedule[-1]["installment_number"] == term
    assert schedule[-1]["closing_balance"] == Decimal("0.00")

    # Verify reconciliation audit
    reconciled, details = verify_schedule_reconciliation(principal, schedule)
    assert reconciled is True
    assert details["is_reconciled"] is True
    assert details["principal_difference"] == Decimal("0.00")
    assert details["total_principal_repaid"] == principal

