from decimal import Decimal, ROUND_HALF_UP


ZERO = Decimal('0.00')
MONEY = Decimal('0.01')


def money(value):
    return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_paye(chargeable_income, *, resident=True, secondary_employment=False):
    """Calculate monthly Uganda PAYE using the current URA resident schedules."""
    income = max(money(chargeable_income), ZERO)
    if secondary_employment:
        return money(income * Decimal('0.30'))

    if resident:
        if income <= Decimal('235000'):
            tax = ZERO
        elif income <= Decimal('335000'):
            tax = (income - Decimal('235000')) * Decimal('0.10')
        elif income <= Decimal('410000'):
            tax = Decimal('10000') + (income - Decimal('335000')) * Decimal('0.20')
        else:
            tax = Decimal('25000') + (income - Decimal('410000')) * Decimal('0.30')
            if income > Decimal('10000000'):
                tax += (income - Decimal('10000000')) * Decimal('0.10')
    else:
        if income <= Decimal('335000'):
            tax = income * Decimal('0.10')
        elif income <= Decimal('410000'):
            tax = Decimal('33500') + (income - Decimal('335000')) * Decimal('0.20')
        else:
            tax = Decimal('48500') + (income - Decimal('410000')) * Decimal('0.30')
            if income > Decimal('10000000'):
                tax += (income - Decimal('10000000')) * Decimal('0.10')
    return money(tax)


def calculate_nssf(gross_wage, *, applicable=True):
    """Return employee and employer NSSF contributions on gross monthly wages."""
    gross = max(money(gross_wage), ZERO)
    if not applicable:
        return {'employee': ZERO, 'employer': ZERO, 'total': ZERO}
    employee = money(gross * Decimal('0.05'))
    employer = money(gross * Decimal('0.10'))
    return {'employee': employee, 'employer': employer, 'total': employee + employer}


def annual_local_service_tax(monthly_income):
    """Return annual LST liability for an employee's monthly income."""
    income = max(money(monthly_income), ZERO)
    brackets = (
        (Decimal('100000'), Decimal('200000'), Decimal('5000')),
        (Decimal('200000'), Decimal('300000'), Decimal('10000')),
        (Decimal('300000'), Decimal('400000'), Decimal('20000')),
        (Decimal('400000'), Decimal('500000'), Decimal('30000')),
        (Decimal('500000'), Decimal('600000'), Decimal('40000')),
        (Decimal('600000'), Decimal('700000'), Decimal('60000')),
        (Decimal('700000'), Decimal('800000'), Decimal('70000')),
        (Decimal('800000'), Decimal('900000'), Decimal('80000')),
        (Decimal('900000'), Decimal('1000000'), Decimal('90000')),
    )
    for lower, upper, annual_tax in brackets:
        if lower < income <= upper:
            return annual_tax
    return Decimal('100000') if income > Decimal('1000000') else ZERO


def calculate_local_service_tax(monthly_income, month, *, applicable=True):
    """Deduct annual LST in four equal instalments from July through October."""
    if not applicable or int(month) not in (7, 8, 9, 10):
        return ZERO
    return money(annual_local_service_tax(monthly_income) / Decimal('4'))


def calculate_statutory_payroll(
    gross_income,
    month,
    *,
    resident=True,
    secondary_employment=False,
    nssf_applicable=True,
    lst_applicable=True,
):
    gross = max(money(gross_income), ZERO)
    lst = calculate_local_service_tax(gross, month, applicable=lst_applicable)
    chargeable_income = max(gross - lst, ZERO)
    paye = calculate_paye(
        chargeable_income,
        resident=resident,
        secondary_employment=secondary_employment,
    )
    nssf = calculate_nssf(gross, applicable=nssf_applicable)
    net_after_statutory = gross - lst - paye - nssf['employee']
    return {
        'gross_income': gross,
        'chargeable_income': chargeable_income,
        'paye': paye,
        'nssf_employee': nssf['employee'],
        'nssf_employer': nssf['employer'],
        'nssf_total': nssf['total'],
        'local_service_tax': lst,
        'net_after_statutory': money(net_after_statutory),
    }
