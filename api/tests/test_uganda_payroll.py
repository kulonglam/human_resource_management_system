from decimal import Decimal

from django.test import SimpleTestCase

from payroll.uganda import (
    annual_local_service_tax,
    calculate_local_service_tax,
    calculate_nssf,
    calculate_paye,
    calculate_statutory_payroll,
)


class UgandaPayrollCalculatorTests(SimpleTestCase):
    def test_resident_monthly_paye_brackets(self):
        cases = (
            ('235000', '0'),
            ('300000', '6500'),
            ('400000', '23000'),
            ('1000000', '202000'),
            ('12000000', '3702000'),
        )
        for income, expected in cases:
            with self.subTest(income=income):
                self.assertEqual(calculate_paye(income), Decimal(expected).quantize(Decimal('0.01')))

    def test_non_resident_and_secondary_employment_paye(self):
        self.assertEqual(calculate_paye('300000', resident=False), Decimal('30000.00'))
        self.assertEqual(
            calculate_paye('1000000', secondary_employment=True),
            Decimal('300000.00'),
        )

    def test_nssf_is_five_percent_employee_and_ten_percent_employer(self):
        result = calculate_nssf('1000000')

        self.assertEqual(result['employee'], Decimal('50000.00'))
        self.assertEqual(result['employer'], Decimal('100000.00'))
        self.assertEqual(result['total'], Decimal('150000.00'))

    def test_local_service_tax_is_deducted_july_through_october(self):
        self.assertEqual(annual_local_service_tax('1200000'), Decimal('100000'))
        self.assertEqual(calculate_local_service_tax('1200000', 7), Decimal('25000.00'))
        self.assertEqual(calculate_local_service_tax('1200000', 11), Decimal('0.00'))

    def test_full_statutory_calculation(self):
        result = calculate_statutory_payroll('1000000', 7)

        self.assertEqual(result['chargeable_income'], Decimal('977500.00'))
        self.assertEqual(result['paye'], Decimal('195250.00'))
        self.assertEqual(result['nssf_employee'], Decimal('50000.00'))
        self.assertEqual(result['nssf_employer'], Decimal('100000.00'))
        self.assertEqual(result['local_service_tax'], Decimal('22500.00'))
        self.assertEqual(result['net_after_statutory'], Decimal('732250.00'))
