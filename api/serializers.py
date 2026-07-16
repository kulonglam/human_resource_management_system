from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.access_control import can_view_sensitive_data, get_user_permissions, mask_sensitive_value
from accounts.models import CustomUser, Role, AuditLog, SensitiveDataAccessLog, Organization
from employees.models import Employee, EmploymentContract, EmploymentHistory, JobGrade, Position
from departments.models import Department


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True, default=None)
    is_admin = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)
    mfa_enabled = serializers.BooleanField(read_only=True)
    mfa_setup_required = serializers.SerializerMethodField()
    linked_employee_id = serializers.SerializerMethodField()
    linked_employee_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_name', 'is_admin', 'is_manager', 'permissions',
            'mfa_enabled', 'mfa_setup_required', 'managed_department',
            'organization', 'linked_employee_id', 'linked_employee_name',
            'is_active', 'date_joined', 'last_login',
        ]
        read_only_fields = fields

    def get_mfa_setup_required(self, obj):
        if obj.mfa_enabled:
            return False
        if obj.is_admin and getattr(settings, 'ENFORCE_MFA_FOR_ADMINS', True):
            return True
        if obj.is_manager and getattr(settings, 'ENFORCE_MFA_FOR_MANAGERS', False):
            return True
        return False

    def get_linked_employee_id(self, obj):
        try:
            return Employee.objects.get(email=obj.email).pk
        except Employee.DoesNotExist:
            return None

    def get_linked_employee_name(self, obj):
        try:
            return Employee.objects.get(email=obj.email).full_name
        except Employee.DoesNotExist:
            return None

    def get_permissions(self, obj):
        return get_user_permissions(obj)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate(self, attrs):
        if not settings.ALLOW_PUBLIC_REGISTRATION:
            raise serializers.ValidationError('Registration is disabled.')
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        employee_role = Role.objects.filter(name=Role.EMPLOYEE).first()
        if employee_role:
            attrs['role'] = employee_role
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.permissions:
            data['permissions'] = instance.resolved_permissions()
        return data


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password']

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'role', 'is_active', 'managed_department']

    def validate(self, attrs):
        request = self.context.get('request')
        instance = self.instance
        if request and instance and instance.pk == request.user.pk:
            if attrs.get('is_active') is False:
                raise serializers.ValidationError({'is_active': 'You cannot deactivate your own account.'})
            if 'role' in attrs and attrs['role'] != instance.role:
                raise serializers.ValidationError({'role': 'You cannot change your own role.'})
        return attrs


class DocumentAccessRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        from documents.models import DocumentAccessRule
        model = DocumentAccessRule
        fields = [
            'id', 'role', 'role_name', 'category', 'category_display',
            'can_view', 'can_upload',
        ]


class SensitiveDataAccessLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = SensitiveDataAccessLog
        fields = [
            'id', 'username', 'employee', 'employee_name', 'fields_accessed',
            'ip_address', 'user_agent', 'accessed_at',
        ]
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'is_active', 'created_at']
        read_only_fields = ['created_at']


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


class EmployeeTerminateSerializer(serializers.Serializer):
    exit_reason = serializers.ChoiceField(choices=Employee.EXIT_REASON_CHOICES)
    exit_notes = serializers.CharField(required=False, allow_blank=True)


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'username', 'action', 'action_display', 'model_name',
            'object_id', 'object_description', 'details', 'ip_address', 'timestamp',
        ]
        read_only_fields = fields
