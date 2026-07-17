"""Payroll domain serializers."""
from rest_framework import serializers

from payroll.models import PayrollRun, Salary

class PayrollRunSerializer(serializers.ModelSerializer):
    period = serializers.CharField(source='__str__', read_only=True)
    employee_count = serializers.IntegerField(source='salary_records.count', read_only=True)
    total_gross = serializers.SerializerMethodField()
    total_net = serializers.SerializerMethodField()
    total_paye = serializers.SerializerMethodField()
    total_nssf = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = [
            'status', 'created_by', 'approved_by', 'approved_at', 'paid_at',
            'created_at', 'updated_at',
        ]

    def _sum(self, obj, field):
        from django.db.models import Sum
        return obj.salary_records.aggregate(value=Sum(field))['value'] or 0

    def get_total_gross(self, obj):
        return self._sum(obj, 'gross_salary')

    def get_total_net(self, obj):
        return self._sum(obj, 'net_salary')

    def get_total_paye(self, obj):
        return self._sum(obj, 'tax')

    def get_total_nssf(self, obj):
        return self._sum(obj, 'nssf_employee') + self._sum(obj, 'nssf_employer')

    def validate_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError('Month must be between 1 and 12.')
        return value



class SalarySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    month_name = serializers.CharField(read_only=True)
    total_earnings = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = Salary
        fields = '__all__'
        read_only_fields = [
            'gross_salary', 'chargeable_income', 'tax', 'nssf_employee',
            'nssf_employer', 'local_service_tax', 'net_salary', 'status',
            'is_paid', 'paid_on', 'payroll_run', 'created_at', 'updated_at',
        ]

    def validate_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError('Month must be between 1 and 12.')
        return value

    def validate_year(self, value):
        if not 2000 <= value <= 2100:
            raise serializers.ValidationError('Enter a valid payroll year.')
        return value



