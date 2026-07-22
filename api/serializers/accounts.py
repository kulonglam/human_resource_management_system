"""Accounts domain serializers."""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.access_control import get_user_permissions
from accounts.models import AuditLog, CustomUser, Notification, Organization, Role, SensitiveDataAccessLog
from api.validation import validate_user_password
from documents.models import HRDocument
from employees.models import Employee
from workflows.models import ApprovalDecision, ApprovalRequest, ApprovalStep, ApprovalWorkflow

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
        candidate = CustomUser(
            username=attrs.get('username', ''),
            email=attrs.get('email', ''),
        )
        try:
            validate_user_password(attrs['password1'], user=candidate)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({'password1': exc.detail}) from exc
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

    def validate_first_name(self, value):
        from api.validation import validate_letters_only
        return validate_letters_only(value, field_label='First name')

    def validate_last_name(self, value):
        from api.validation import validate_letters_only
        return validate_letters_only(value, field_label='Last name')

    def validate_password(self, value):
        candidate = CustomUser(
            username=self.initial_data.get('username', ''),
            email=self.initial_data.get('email', ''),
            first_name=self.initial_data.get('first_name', ''),
            last_name=self.initial_data.get('last_name', ''),
        )
        return validate_user_password(value, user=candidate)

    def create(self, validated_data):
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)



class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'role', 'is_active', 'managed_department']

    def validate_first_name(self, value):
        from api.validation import validate_letters_only
        if value is None or value == '':
            return value
        return validate_letters_only(value, field_label='First name')

    def validate_last_name(self, value):
        from api.validation import validate_letters_only
        if value is None or value == '':
            return value
        return validate_letters_only(value, field_label='Last name')

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

class ApprovalStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalStep
        fields = ['id', 'step_order', 'label', 'approver_type']



class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalWorkflow
        fields = [
            'id', 'name', 'workflow_type', 'is_default', 'is_active',
            'extra_step_min_days', 'extra_step_min_amount', 'steps',
        ]



class ApprovalDecisionSerializer(serializers.ModelSerializer):
    decided_by_name = serializers.CharField(source='decided_by.username', read_only=True, default=None)

    class Meta:
        model = ApprovalDecision
        fields = [
            'id', 'step_order', 'step_label', 'decided_by_name',
            'decision', 'comment', 'decided_at',
        ]



class ApprovalRequestSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    workflow_type = serializers.CharField(source='workflow.workflow_type', read_only=True)
    object_type = serializers.SerializerMethodField()
    object_id = serializers.IntegerField(read_only=True)
    object_repr = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()
    detail_link = serializers.SerializerMethodField()
    submitted_by_name = serializers.CharField(source='submitted_by.username', read_only=True, default=None)
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'workflow_name', 'workflow_type', 'status', 'current_step_order',
            'object_type', 'object_id', 'object_repr', 'summary', 'current_step',
            'detail_link', 'submitted_by_name', 'submitted_at', 'completed_at', 'decisions',
        ]

    def get_object_type(self, obj):
        return obj.content_type.model if obj.content_type_id else None

    def get_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else f'#{obj.object_id}'

    def get_summary(self, obj):
        target = obj.content_object
        if target is None:
            return f'Item #{obj.object_id}'
        workflow_type = obj.workflow.workflow_type
        if workflow_type == 'leave':
            return (
                f'{target.employee.full_name} — {target.get_leave_type_display()} '
                f'({target.start_date} to {target.end_date}, {target.duration} days)'
            )
        if workflow_type == 'expense':
            return f'{target.employee.full_name} — {target.description} (UGX {target.amount})'
        if workflow_type == 'recruitment':
            return f'{target.first_name} {target.last_name} — {target.job.title}'
        return str(target)

    def get_current_step(self, obj):
        from workflows.services import _current_step
        step = _current_step(obj)
        return step.label if step else None

    def get_detail_link(self, obj):
        target = obj.content_object
        workflow_type = obj.workflow.workflow_type
        if workflow_type == 'leave':
            return '/leaves'
        if workflow_type == 'expense':
            return '/expenses'
        if workflow_type == 'recruitment' and target is not None:
            return f'/recruitment/jobs/{target.job_id}'
        return '/approvals'



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'category', 'link', 'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'message', 'category', 'link', 'created_at']



class HRDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, default=None)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, default=None)
    file_url = serializers.SerializerMethodField()
    acknowledged = serializers.SerializerMethodField()
    acknowledgement_count = serializers.SerializerMethodField()

    class Meta:
        model = HRDocument
        fields = [
            'id', 'title', 'category', 'category_display', 'description', 'file', 'file_url',
            'employee', 'employee_name', 'version', 'is_active',
            'requires_acknowledgement', 'expires_at', 'legal_hold',
            'acknowledged', 'acknowledgement_count',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']

    def get_acknowledged(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        try:
            from employees.models import Employee
            from documents.models import DocumentAcknowledgement

            employee = Employee.objects.get(email=request.user.email)
            return DocumentAcknowledgement.objects.filter(document=obj, employee=employee).exists()
        except Exception:
            return False

    def get_acknowledgement_count(self, obj):
        return obj.acknowledgements.count()

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

