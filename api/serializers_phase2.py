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
    object_repr = serializers.SerializerMethodField()
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'workflow_name', 'status', 'current_step_order',
            'object_repr', 'submitted_at', 'completed_at', 'decisions',
        ]

    def get_object_repr(self, obj):
        return str(obj.content_object) if obj.content_object else f'#{obj.object_id}'


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

    class Meta:
        model = HRDocument
        fields = [
            'id', 'title', 'category', 'category_display', 'description', 'file', 'file_url',
            'employee', 'employee_name', 'version', 'is_active',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at']

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
