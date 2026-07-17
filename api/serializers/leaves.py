"""Leaves domain serializers."""
from rest_framework import serializers

from accounts.access_control import can_access_employee
from employees.models import Employee
from leave_policies.models import LeavePolicy, LeavePolicyAllocation
from leaves.models import Leave, LeaveBalance
from workflows.services import approval_status_payload

class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    duration = serializers.FloatField(source='working_days', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_status = serializers.SerializerMethodField()

    class Meta:
        model = Leave
        fields = '__all__'
        read_only_fields = ['status', 'applied_on', 'reviewed_by', 'reviewed_on', 'working_days']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_admin and not request.user.is_manager:
            self.fields['employee'].required = False

    def get_approval_status(self, obj):
        return approval_status_payload(obj)

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            if user.is_admin or user.is_manager:
                employee = attrs.get('employee')
                if employee and not can_access_employee(user, employee):
                    raise serializers.ValidationError({'employee': 'You cannot create leave for this employee.'})
            else:
                try:
                    own_employee = Employee.objects.get(email=user.email)
                except Employee.DoesNotExist:
                    raise serializers.ValidationError(
                        {'employee': 'No employee profile is linked to your account.'},
                    )

                employee = attrs.get('employee')
                if employee and employee.pk != own_employee.pk:
                    raise serializers.ValidationError({'employee': 'You can only apply leave for yourself.'})
                attrs['employee'] = own_employee

        start_date = attrs.get('start_date') or getattr(self.instance, 'start_date', None)
        end_date = attrs.get('end_date') or getattr(self.instance, 'end_date', None)
        is_half_day = attrs.get('is_half_day', getattr(self.instance, 'is_half_day', False))
        leave_type = attrs.get('leave_type') or getattr(self.instance, 'leave_type', None)
        employee = attrs.get('employee') or getattr(self.instance, 'employee', None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date.'})

        working_days = None
        if start_date and end_date:
            if is_half_day and start_date != end_date:
                raise serializers.ValidationError(
                    {'is_half_day': 'Half-day leave must use the same start and end date.'},
                )
            from leaves.services import calculate_leave_duration

            working_days = calculate_leave_duration(start_date, end_date, is_half_day=is_half_day)
            if working_days <= 0:
                raise serializers.ValidationError(
                    {'start_date': 'Selected dates contain no working days.'},
                )
            attrs['_computed_working_days'] = working_days

        if employee and start_date and end_date:
            from api.validation import leave_date_ranges_overlap
            from leaves.models import Leave

            overlap_qs = Leave.objects.filter(
                employee=employee,
                status__in=['pending', 'approved'],
            )
            if self.instance:
                overlap_qs = overlap_qs.exclude(pk=self.instance.pk)
            for other in overlap_qs.only('start_date', 'end_date', 'id'):
                if leave_date_ranges_overlap(start_date, end_date, other.start_date, other.end_date):
                    raise serializers.ValidationError({
                        'start_date': (
                            f'Overlaps existing {other.status} leave '
                            f'({other.start_date} – {other.end_date}).'
                        ),
                    })

        # Unpaid leave does not consume balance; all other types require an allocation.
        if leave_type and leave_type != 'unpaid' and employee and working_days is not None:
            from django.utils import timezone
            from leaves.models import LeaveBalance

            year = start_date.year if start_date else timezone.now().year
            try:
                balance = LeaveBalance.objects.get(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                )
            except LeaveBalance.DoesNotExist as exc:
                raise serializers.ValidationError({
                    'leave_type': (
                        f'No {leave_type} leave balance for {year}. '
                        'Ask HR to allocate leave days first.'
                    ),
                }) from exc
            if balance.available_days < working_days:
                raise serializers.ValidationError({
                    'leave_type': (
                        f'Insufficient leave balance. Available: {balance.available_days} days, '
                        f'requested: {working_days}.'
                    ),
                })
            attrs['_leave_balance'] = balance

        return attrs

    def create(self, validated_data):
        validated_data.pop('_leave_balance', None)
        validated_data.pop('_computed_working_days', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('_leave_balance', None)
        validated_data.pop('_computed_working_days', None)
        return super().update(instance, validated_data)



class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    available_days = serializers.FloatField(read_only=True)

    class Meta:
        model = LeaveBalance
        fields = '__all__'



class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)

    class Meta:
        model = LeavePolicy
        fields = '__all__'



class LeavePolicyAllocationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)

    class Meta:
        model = LeavePolicyAllocation
        fields = '__all__'



