from rest_framework import serializers

from accounts.models import Notification
from documents.models import HRDocument
from workflows.models import ApprovalDecision, ApprovalRequest, ApprovalStep, ApprovalWorkflow
from workflows.services import approval_status_payload


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


class ApprovalStatusMixin(serializers.Serializer):
    approval_status = serializers.SerializerMethodField()

    def get_approval_status(self, obj):
        return approval_status_payload(obj)
