"""Employees domain serializers."""
from rest_framework import serializers

from accounts.access_control import can_view_sensitive_data, mask_sensitive_value
from api.validation import parse_positive_decimal, validate_employee_dates, validate_mobile_number
from departments.models import Department
from employees.models import Employee, EmploymentContract, EmploymentHistory, JobGrade, Position

class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()
    parent_name = serializers.CharField(source='parent.name', read_only=True, default=None)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'location', 'history', 'parent', 'parent_name',
            'manager_name', 'manager_contact', 'created_at', 'employee_count',
        ]

    def get_employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()



class JobGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobGrade
        fields = '__all__'



class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    grade_name = serializers.CharField(source='grade.name', read_only=True, default=None)
    reports_to_title = serializers.CharField(source='reports_to.title', read_only=True, default=None)

    class Meta:
        model = Position
        fields = '__all__'



class EmploymentContractSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = EmploymentContract
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



class EmploymentHistorySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = EmploymentHistory
        fields = '__all__'
        read_only_fields = ['recorded_by', 'created_at']



class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    position_title = serializers.CharField(source='position.title', read_only=True, default=None)
    grade_name = serializers.CharField(source='grade.name', read_only=True, default=None)
    supervisor_name = serializers.CharField(source='supervisor.full_name', read_only=True, default=None)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_number', 'photo', 'photo_url', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'gender', 'email', 'mobile', 'address',
            'emergency_contact', 'language', 'national_id_number',
            'tax_identification_number', 'nssf_number', 'job_title', 'department',
            'department_name', 'position', 'position_title', 'grade', 'grade_name',
            'supervisor', 'supervisor_name', 'employment_type', 'date_joined',
            'probation_end_date', 'work_location', 'cost_center', 'is_active', 'account_number',
            'bank', 'salary', 'termination_date', 'exit_reason', 'exit_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'employee_number', 'created_at', 'updated_at', 'termination_date',
            'exit_reason', 'exit_notes',
        ]

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if user and not can_view_sensitive_data(user):
            for field in (
                'account_number', 'bank', 'salary',
                'national_id_number', 'tax_identification_number', 'nssf_number',
            ):
                if data.get(field):
                    data[field] = mask_sensitive_value(data[field])
        return data

    def validate_mobile(self, value):
        return validate_mobile_number(value)

    def validate_salary(self, value):
        return parse_positive_decimal(value, field_name='salary')

    def validate(self, attrs):
        validate_employee_dates(attrs, instance=self.instance)
        return attrs



class EmployeeTerminateSerializer(serializers.Serializer):
    exit_reason = serializers.ChoiceField(choices=Employee.EXIT_REASON_CHOICES)
    exit_notes = serializers.CharField(required=False, allow_blank=True)



