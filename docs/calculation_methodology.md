# Calculation Methodology & Financial Math Engine

## 1. Mathematical Formulas

### 1.1 Debt-to-Income (DTI) Ratio
Measures existing recurring monthly debt servicing obligations as a proportion of gross monthly earnings:

$$\text{DTI} = \left(\frac{\text{Existing Monthly Debt Obligations}}{\text{Monthly Gross Income}}\right) \times 100$$

- **Zero Division Safeguard**: If gross income $\le 0$, DTI evaluates to $100.00\%$ if debt $> 0$, or $0.00\%$ if debt $= 0$.
- **Rounding**: Standard financial quantizing to 2 decimal places (`ROUND_HALF_UP`).

---

### 1.2 Fixed Obligation to Income Ratio (FOIR)
Measures total debt servicing obligations (existing debt plus the proposed new loan EMI) relative to net in-hand monthly income:

$$\text{FOIR} = \left(\frac{\text{Existing Monthly Debt Obligations} + \text{Proposed Monthly EMI}}{\text{Monthly Net Income}}\right) \times 100$$

- **Zero Division Safeguard**: If net income $\le 0$, FOIR evaluates to $100.00\%$ if obligations $> 0$, or $0.00\%$ otherwise.

---

### 1.3 Disposable Monthly Income
Determines the unencumbered cash flow remaining after servicing all existing and proposed obligations:

$$\text{Disposable Income} = \text{Monthly Net Income} - \text{Existing Debt} - \text{Proposed EMI}$$

---

### 1.4 Reducing-Balance Monthly EMI
The installment is amortized according to the standard reducing balance compounding formula:

$$\text{EMI} = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}$$

Where:
- $P$ = Disbursed Principal
- $r = \frac{\text{Annual Interest Rate}}{12 \times 100}$ (Monthly fractional interest rate)
- $n = \text{Requested Term in Months}$

#### Zero-Interest Support ($r = 0$):
When financing at zero interest ($0.00\%$ APR):

$$\text{EMI} = \frac{P}{n}$$

---

## 2. Repayment Schedule Amortization & Penny-Rounding Reconciliation

To guarantee mathematical integrity in banking audits, the amortization engine guarantees:

1. For each monthly cycle $i \in \{1, \dots, n\}$:
   $$\text{Interest}_i = \text{round}(\text{Opening Balance}_i \times r, 2)$$
   $$\text{Principal}_i = \text{Installment Amount}_i - \text{Interest}_i$$
   $$\text{Closing Balance}_i = \text{Opening Balance}_i - \text{Principal}_i$$
2. **Final Installment Adjustment ($i = n$)**:
   $$\text{Principal}_n = \text{Opening Balance}_n$$
   $$\text{Installment Amount}_n = \text{Principal}_n + \text{Interest}_n$$
   $$\text{Closing Balance}_n = 0.00$$
3. **Audit Reconciliation Checks**:
   - $\left|\sum_{i=1}^n \text{Principal}_i - P\right| \le 0.05$ INR
   - $\sum_{i=1}^n \text{Installment Amount}_i = P + \sum_{i=1}^n \text{Interest}_i$
   - No negative balances permitted.

