from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from payroll.models import Salary

from .permissions import IsAdminOrManager
from .report_exports import export_rows_csv, export_rows_xlsx


class PayrollExportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        export_format = request.query_params.get('format', 'xlsx').lower()

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
                'month', 'year', 'basic_salary', 'allowances', 'deductions', 'tax', 'net_salary',
                'payment_method', 'is_paid',
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
            {'key': 'deductions', 'label': 'Deductions'},
            {'key': 'tax', 'label': 'Tax'},
            {'key': 'net_salary', 'label': 'Net Salary'},
            {'key': 'payment_method', 'label': 'Payment Method'},
            {'key': 'is_paid', 'label': 'Paid'},
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
