from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from payroll.models import Salary

from .permissions import HasAPIKeyScope, IsPayrollUser, RequiresMFAForPayroll
from .report_exports import export_rows_csv, export_rows_xlsx
from .throttles import ExportRateThrottle


class PayrollExportView(APIView):
    permission_classes = [IsPayrollUser, RequiresMFAForPayroll, HasAPIKeyScope]
    throttle_classes = [ExportRateThrottle]
    required_api_scopes = ['payroll', 'export', 'admin']

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        export_format = request.query_params.get(
            'export_format', request.query_params.get('format', 'xlsx')
        ).lower()

        qs = Salary.objects.filter(month=month, year=year).select_related('employee', 'employee__department')
        department = request.query_params.get('department')
        if department:
            qs = qs.filter(employee__department_id=department)

        rows = list(
            qs.annotate(
                employee_name=F('employee__first_name'),
                employee_last_name=F('employee__last_name'),
                department_name=F('employee__department__name'),
            ).values(
                'employee_name', 'employee_last_name', 'department_name',
                'month', 'year', 'basic_salary', 'allowances', 'taxable_benefits',
                'gross_salary', 'chargeable_income', 'tax', 'nssf_employee',
                'nssf_employer', 'local_service_tax', 'deductions', 'net_salary',
                'payment_method', 'status', 'paid_on',
            )
        )
        for row in rows:
            row['employee'] = f"{row.pop('employee_name', '')} {row.pop('employee_last_name', '')}".strip()

        columns = [
            {'key': 'employee', 'label': 'Employee'},
            {'key': 'department_name', 'label': 'Department'},
            {'key': 'month', 'label': 'Month'},
            {'key': 'year', 'label': 'Year'},
            {'key': 'basic_salary', 'label': 'Basic Salary'},
            {'key': 'allowances', 'label': 'Allowances'},
            {'key': 'taxable_benefits', 'label': 'Taxable Benefits'},
            {'key': 'gross_salary', 'label': 'Gross Salary'},
            {'key': 'chargeable_income', 'label': 'PAYE Chargeable Income'},
            {'key': 'tax', 'label': 'PAYE'},
            {'key': 'nssf_employee', 'label': 'Employee NSSF (5%)'},
            {'key': 'nssf_employer', 'label': 'Employer NSSF (10%)'},
            {'key': 'local_service_tax', 'label': 'Local Service Tax'},
            {'key': 'deductions', 'label': 'Deductions'},
            {'key': 'net_salary', 'label': 'Net Salary'},
            {'key': 'payment_method', 'label': 'Payment Method'},
            {'key': 'status', 'label': 'Status'},
            {'key': 'paid_on', 'label': 'Paid On'},
        ]

        if export_format == 'json':
            totals = qs.aggregate(
                total_net=Sum('net_salary'),
                total_gross=Sum(F('basic_salary') + F('allowances')),
            )
            return Response({
                'period': f'{month}/{year}',
                'count': len(rows),
                'total_net': totals['total_net'] or 0,
                'total_gross': totals['total_gross'] or 0,
                'rows': rows,
            })

        if export_format == 'csv':
            return export_rows_csv(rows, columns, 'payroll_export')
        return export_rows_xlsx(rows, columns, 'payroll_export', 'Payroll')


class StatutoryPayrollExportView(APIView):
    """Export PAYE or NSSF filing rows for a payroll period."""

    permission_classes = [IsPayrollUser, RequiresMFAForPayroll, HasAPIKeyScope]
    throttle_classes = [ExportRateThrottle]
    required_api_scopes = ['payroll', 'export', 'admin']

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        return_type = request.query_params.get('return_type', 'paye').lower()
        export_format = request.query_params.get('export_format', 'csv').lower()

        qs = Salary.objects.filter(month=month, year=year).select_related('employee')
        if return_type == 'nssf':
            rows = [
                {
                    'employee_number': salary.employee.employee_number,
                    'employee_name': salary.employee.full_name,
                    'nssf_number': salary.employee.nssf_number or '',
                    'gross_salary': salary.gross_salary,
                    'nssf_employee': salary.nssf_employee,
                    'nssf_employer': salary.nssf_employer,
                    'month': month,
                    'year': year,
                }
                for salary in qs
            ]
            columns = [
                {'key': 'employee_number', 'label': 'Employee No.'},
                {'key': 'employee_name', 'label': 'Employee Name'},
                {'key': 'nssf_number', 'label': 'NSSF Number'},
                {'key': 'gross_salary', 'label': 'Gross Salary (UGX)'},
                {'key': 'nssf_employee', 'label': 'Employee NSSF (5%)'},
                {'key': 'nssf_employer', 'label': 'Employer NSSF (10%)'},
                {'key': 'month', 'label': 'Month'},
                {'key': 'year', 'label': 'Year'},
            ]
            title = 'NSSF_Return'
        else:
            rows = [
                {
                    'employee_number': salary.employee.employee_number,
                    'employee_name': salary.employee.full_name,
                    'tin': salary.employee.tax_identification_number or '',
                    'chargeable_income': salary.chargeable_income,
                    'paye': salary.tax,
                    'month': month,
                    'year': year,
                }
                for salary in qs
            ]
            columns = [
                {'key': 'employee_number', 'label': 'Employee No.'},
                {'key': 'employee_name', 'label': 'Employee Name'},
                {'key': 'tin', 'label': 'TIN'},
                {'key': 'chargeable_income', 'label': 'Chargeable Income (UGX)'},
                {'key': 'paye', 'label': 'PAYE (UGX)'},
                {'key': 'month', 'label': 'Month'},
                {'key': 'year', 'label': 'Year'},
            ]
            title = 'PAYE_Return'

        if export_format == 'json':
            return Response({'return_type': return_type, 'period': f'{month}/{year}', 'rows': rows})
        if export_format == 'ura' and return_type == 'paye':
            ura_rows = [
                {
                    'tin': row['tin'],
                    'taxpayer_name': row['employee_name'],
                    'gross_emoluments': salary.gross_salary,
                    'chargeable_income': row['chargeable_income'],
                    'tax_deducted': row['paye'],
                    'period': f'{year}-{month:02d}',
                }
                for row, salary in zip(rows, qs)
            ]
            ura_columns = [
                {'key': 'tin', 'label': 'TIN'},
                {'key': 'taxpayer_name', 'label': 'Taxpayer Name'},
                {'key': 'gross_emoluments', 'label': 'Gross Emoluments (UGX)'},
                {'key': 'chargeable_income', 'label': 'Chargeable Income (UGX)'},
                {'key': 'tax_deducted', 'label': 'Tax Deducted (UGX)'},
                {'key': 'period', 'label': 'Period (YYYY-MM)'},
            ]
            return export_rows_csv(ura_rows, ura_columns, f'URA_PAYE_{year}_{month:02d}')
        if export_format == 'xlsx':
            return export_rows_xlsx(rows, columns, title, title.replace('_', ' '))
        return export_rows_csv(rows, columns, title)
