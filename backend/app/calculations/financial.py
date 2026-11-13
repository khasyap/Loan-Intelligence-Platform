"""
Financial Calculation Engine: Pure, deterministic calculations for:
1. Existing Debt-to-Gross-Income (Existing DTI)
2. Total Debt-to-Gross-Income including proposed EMI (Total DTI)
3. Fixed Obligation to Net-Income Ratio (FOIR)
4. Disposable Monthly Income
5. Reducing-balance Monthly EMI & Zero-Interest financing
6. Penny-reconciled repayment amortization & principal verification.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional
import datetime

def quantize_currency(value: Decimal | float | None) -> Decimal:
    """Safely converts to Decimal and rounds to 2 decimal places using ROUND_HALF_UP."""
    if value is None:
        return Decimal("0.00")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_existing_dti(
    existing_monthly_debt: Decimal | float | None,
    gross_monthly_income: Decimal | float | None
) -> Decimal:
    """
    Existing DTI = (Existing Monthly Debt Obligations / Monthly Gross Income) * 100
    Guards explicitly against zero or missing income.
    """
    debt = max(Decimal("0.00"), Decimal(str(existing_monthly_debt or 0)))
    income = max(Decimal("0.00"), Decimal(str(gross_monthly_income or 0)))

    if income <= Decimal("0.00"):
        return Decimal("100.00") if debt > Decimal("0.00") else Decimal("0.00")

    dti = (debt / income) * Decimal("100.00")
    return quantize_currency(dti)


# Alias for backward compatibility
calculate_dti = calculate_existing_dti


def calculate_total_dti(
    existing_monthly_debt: Decimal | float | None,
    proposed_monthly_emi: Decimal | float | None,
    gross_monthly_income: Decimal | float | None
) -> Decimal:
    """
    Total DTI = ((Existing Monthly Debt + Proposed Monthly EMI) / Monthly Gross Income) * 100
    Evaluates comprehensive debt burden relative to gross income.
    """
    debt = max(Decimal("0.00"), Decimal(str(existing_monthly_debt or 0)))
    emi = max(Decimal("0.00"), Decimal(str(proposed_monthly_emi or 0)))
    income = max(Decimal("0.00"), Decimal(str(gross_monthly_income or 0)))
    total_debt = debt + emi

    if income <= Decimal("0.00"):
        return Decimal("100.00") if total_debt > Decimal("0.00") else Decimal("0.00")

    total_dti = (total_debt / income) * Decimal("100.00")
    return quantize_currency(total_dti)


def calculate_foir(
    existing_monthly_debt: Decimal | float | None,
    proposed_monthly_emi: Decimal | float | None,
    net_monthly_income: Decimal | float | None
) -> Decimal:
    """
    FOIR = ((Existing Monthly Debt + Proposed Monthly EMI) / Monthly Net Income) * 100
    Measures total recurring debt obligations relative to take-home pay.
    """
    debt = max(Decimal("0.00"), Decimal(str(existing_monthly_debt or 0)))
    emi = max(Decimal("0.00"), Decimal(str(proposed_monthly_emi or 0)))
    income = max(Decimal("0.00"), Decimal(str(net_monthly_income or 0)))
    total_obligations = debt + emi

    if income <= Decimal("0.00"):
        return Decimal("100.00") if total_obligations > Decimal("0.00") else Decimal("0.00")

    foir = (total_obligations / income) * Decimal("100.00")
    return quantize_currency(foir)


def calculate_disposable_income(
    net_monthly_income: Decimal | float | None,
    existing_monthly_debt: Decimal | float | None,
    proposed_monthly_emi: Decimal | float | None
) -> Decimal:
    """
    Disposable Income = Monthly Net Income - Existing Monthly Debt - Proposed Monthly EMI
    Can be negative if obligations exceed take-home earnings.
    """
    income = Decimal(str(net_monthly_income or 0))
    debt = Decimal(str(existing_monthly_debt or 0))
    emi = Decimal(str(proposed_monthly_emi or 0))
    return quantize_currency(income - debt - emi)


def calculate_reducing_emi(
    principal: Decimal | float | None,
    annual_interest_rate: Decimal | float | None,
    term_months: int
) -> Decimal:
    """
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    Zero-interest loans (r = 0): EMI = P / n.
    """
    P = max(Decimal("0.00"), Decimal(str(principal or 0)))
    annual_rate = max(Decimal("0.00"), Decimal(str(annual_interest_rate or 0)))
    n = int(term_months)

    if n <= 0:
        raise ValueError("Loan term in months must be greater than zero.")
    if P <= Decimal("0.00"):
        return Decimal("0.00")

    if annual_rate == Decimal("0.00"):
        return quantize_currency(P / Decimal(str(n)))

    # Monthly fractional interest rate
    r = (annual_rate / Decimal("100.00")) / Decimal("12.00")
    r_float = float(r)
    factor = (1.0 + r_float) ** n
    numerator = float(P) * r_float * factor
    denominator = factor - 1.0

    if denominator == 0:
        return quantize_currency(P / Decimal(str(n)))

    emi_val = Decimal(str(numerator / denominator))
    return quantize_currency(emi_val)


def generate_amortization_schedule(
    application_id: str,
    principal: Decimal | float,
    annual_interest_rate: Decimal | float,
    term_months: int,
    disbursement_date: datetime.date
) -> List[Dict[str, Any]]:
    """
    Generates a monthly repayment schedule with penny-rounding reconciliation.
    Guarantees:
    - Sum of principal repayments == principal
    - Sum of installments == principal + total interest
    - Final installment adjusts for rounding to bring closing balance to 0.00
    - Contiguous installment numbers 1 to term_months
    """
    P = quantize_currency(principal)
    annual_rate = Decimal(str(annual_interest_rate))
    n = term_months

    if n <= 0:
        raise ValueError("Term months must be positive.")

    monthly_emi = calculate_reducing_emi(P, annual_rate, n)
    monthly_r = (annual_rate / Decimal("100.00")) / Decimal("12.00")

    installments = []
    opening_bal = P

    cur_year = disbursement_date.year
    cur_month = disbursement_date.month

    for i in range(1, n + 1):
        cur_month += 1
        if cur_month > 12:
            cur_month = 1
            cur_year += 1

        due_day = min(disbursement_date.day, 28)
        due_date = datetime.date(cur_year, cur_month, due_day)

        if annual_rate == Decimal("0.00"):
            interest_amount = Decimal("0.00")
        else:
            interest_amount = quantize_currency(opening_bal * monthly_r)

        if i == n:
            principal_amount = opening_bal
            installment_amount = quantize_currency(principal_amount + interest_amount)
            closing_bal = Decimal("0.00")
        else:
            principal_amount = quantize_currency(monthly_emi - interest_amount)
            if principal_amount > opening_bal:
                principal_amount = opening_bal
            installment_amount = quantize_currency(principal_amount + interest_amount)
            closing_bal = quantize_currency(opening_bal - principal_amount)

        schedule_id = f"SCH-{application_id}-{i:03d}"
        installments.append({
            "schedule_id": schedule_id,
            "application_id": application_id,
            "installment_number": i,
            "due_date": due_date,
            "opening_balance": opening_bal,
            "principal_amount": principal_amount,
            "interest_amount": interest_amount,
            "installment_amount": installment_amount,
            "closing_balance": closing_bal,
            "payment_status": "SCHEDULED",
            "paid_amount": Decimal("0.00"),
            "paid_date": None
        })

        opening_bal = closing_bal

    return installments


def verify_schedule_reconciliation(
    principal: Decimal | float,
    installments: List[Dict[str, Any]],
    tolerance: Decimal = Decimal("0.05")
) -> Tuple[bool, Dict[str, Any]]:
    """
    Audits an amortization schedule to verify:
    1. Sum of principal repayments == principal
    2. Sum of installment amounts == total principal + total interest
    3. Final closing balance == 0.00
    4. No negative balances
    """
    target_p = quantize_currency(principal)
    total_principal_repaid = sum(Decimal(str(inst["principal_amount"])) for inst in installments)
    total_interest = sum(Decimal(str(inst["interest_amount"])) for inst in installments)
    total_installments = sum(Decimal(str(inst["installment_amount"])) for inst in installments)

    principal_diff = abs(total_principal_repaid - target_p)
    reconciled = (principal_diff <= tolerance) and (installments[-1]["closing_balance"] == Decimal("0.00"))

    details = {
        "disbursed_principal": target_p,
        "total_principal_repaid": total_principal_repaid,
        "total_interest": total_interest,
        "total_installments": total_installments,
        "principal_difference": principal_diff,
        "final_closing_balance": installments[-1]["closing_balance"] if installments else None,
        "is_reconciled": reconciled
    }
    return reconciled, details
