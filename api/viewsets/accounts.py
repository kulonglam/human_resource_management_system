"""Accounts domain HTTP adapters."""
from django.db.models import Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import AuditLog, CustomUser, Role
from api.audit import log_action
from api.mixins import AuditedModelViewSet
from api.permissions import IsAdmin, IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import AuditLogSerializer
from api.serializers.accounts import (
    ApprovalRequestSerializer,
    ApprovalWorkflowSerializer,
    HRDocumentSerializer,
    NotificationSerializer,
)
from employees.models import Employee


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-timestamp')

    @action(detail=False, methods=['get'], url_path='export')
    def export_logs(self, request):
        from api.compliance_views import audit_log_export_response
        return audit_log_export_response(request)


class NotificationViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'patch', 'head', 'options', 'post']
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return self.request.user.notifications.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'marked_read': updated})


class HRDocumentViewSet(AuditedModelViewSet):
    serializer_class = HRDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        from documents.access_control import filter_documents_for_user
        from documents.models import HRDocument

        qs = HRDocument.objects.filter(is_active=True).select_related('employee', 'uploaded_by')
        qs = filter_documents_for_user(qs, self.request.user)
        if not self.request.user.is_admin:
            try:
                employee = Employee.objects.get(email=self.request.user.email)
                qs = qs.filter(Q(employee=employee) | Q(employee__isnull=True))
            except Employee.DoesNotExist:
                qs = qs.filter(employee__isnull=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        return qs.order_by('-created_at')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminOrManagerOrReadOnly()]

    def perform_create(self, serializer):
        from documents.access_control import user_can_upload_document_category
        from api.uploads import validate_upload

        category = serializer.validated_data.get('category', 'other')
        if not user_can_upload_document_category(self.request.user, category):
            raise serializers.ValidationError({'category': 'You cannot upload documents in this category.'})
        upload = serializer.validated_data.get('file')
        if upload:
            validate_upload(upload, kind='document')
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        from documents.models import DocumentAcknowledgement

        document = self.get_object()
        if not document.requires_acknowledgement:
            return Response({'detail': 'This document does not require acknowledgement.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            employee = Employee.objects.get(email=request.user.email)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee profile linked to your account.'}, status=status.HTTP_400_BAD_REQUEST)

        acknowledgement, created = DocumentAcknowledgement.objects.get_or_create(
            document=document,
            employee=employee,
            defaults={'ip_address': request.META.get('REMOTE_ADDR')},
        )
        return Response({
            'acknowledged': True,
            'created': created,
            'document': HRDocumentSerializer(document, context={'request': request}).data,
        })


class ApprovalWorkflowViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalWorkflowSerializer

    def get_queryset(self):
        from workflows.models import ApprovalWorkflow
        return ApprovalWorkflow.objects.filter(is_active=True).prefetch_related('steps')

    def get_permissions(self):
        return [IsAdminOrManagerOrReadOnly()]


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalRequestSerializer

    def get_permissions(self):
        return [IsAdminOrManager()]

    def get_queryset(self):
        from workflows.models import ApprovalRequest
        from workflows.services import get_pending_for_user

        status_filter = self.request.query_params.get('status', 'pending')
        scope = self.request.query_params.get('scope', 'mine')

        if scope == 'all' and self.request.user.is_admin:
            qs = ApprovalRequest.objects.select_related(
                'workflow', 'content_type', 'submitted_by',
            ).prefetch_related('decisions')
        else:
            qs = get_pending_for_user(self.request.user)

        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-submitted_at')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        from api.approval_integration import process_approval_request_decision

        approval_request = self.get_object()
        outcome = process_approval_request_decision(
            request, approval_request, True, request.data.get('comment', ''),
        )
        if outcome.get('status') == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome.get('status') == 404:
            return Response({'detail': outcome['detail']}, status=status.HTTP_404_NOT_FOUND)
        if outcome.get('status') == 400:
            return Response({'detail': outcome['detail']}, status=status.HTTP_400_BAD_REQUEST)

        approval_request.refresh_from_db()
        return Response({
            'result': outcome.get('result'),
            'approval_request': ApprovalRequestSerializer(approval_request, context={'request': request}).data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        from api.approval_integration import process_approval_request_decision

        approval_request = self.get_object()
        comment = request.data.get('comment', request.data.get('reason', ''))
        outcome = process_approval_request_decision(
            request, approval_request, False, comment,
        )
        if outcome.get('status') == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        if outcome.get('status') == 404:
            return Response({'detail': outcome['detail']}, status=status.HTTP_404_NOT_FOUND)
        if outcome.get('status') == 400:
            return Response({'detail': outcome['detail']}, status=status.HTTP_400_BAD_REQUEST)

        approval_request.refresh_from_db()
        return Response({
            'result': outcome.get('result'),
            'approval_request': ApprovalRequestSerializer(approval_request, context={'request': request}).data,
        })


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        from api.serializers import RoleSerializer
        return RoleSerializer

    def get_permissions(self):
        from django.conf import settings
        from rest_framework.permissions import AllowAny

        if self.action == 'list' and getattr(settings, 'ALLOW_PUBLIC_REGISTRATION', False):
            return [AllowAny()]
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [IsAdmin()]

    def partial_update(self, request, *args, **kwargs):
        role = self.get_object()
        if role.name == Role.ADMIN:
            return Response({'detail': 'Admin role permissions cannot be changed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_action(request, 'update', 'Role', role.id, role.name, 'Role permissions updated')
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        qs = CustomUser.objects.select_related('role').order_by('username')
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id:
            qs = qs.filter(Q(organization_id=org_id) | Q(organization__isnull=True))
        if self.request.user.is_admin and self.request.query_params.get('include_inactive') == '1':
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self):
        if self.action in ('create', 'partial_update', 'update'):
            return [IsAdmin()]
        if self.action in ('list', 'retrieve'):
            return [IsAdminOrManager()]
        return [IsAdmin()]

    def get_serializer_class(self):
        from api.serializers import AdminUserCreateSerializer, AdminUserUpdateSerializer, UserSerializer
        if self.action == 'create':
            return AdminUserCreateSerializer
        if self.action in ('partial_update', 'update'):
            return AdminUserUpdateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        from api.serializers import UserSerializer

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(request, 'create', 'CustomUser', user.id, user.username, 'User created by admin')
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        from api.serializers import UserSerializer

        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        if 'is_active' in serializer.validated_data and not updated.is_active:
            Employee.objects.filter(email=updated.email).update(is_active=False)
            log_action(request, 'update', 'CustomUser', updated.id, updated.username, 'User deactivated')
        else:
            log_action(request, 'update', 'CustomUser', updated.id, updated.username, 'User updated by admin')
        return Response(UserSerializer(updated, context=self.get_serializer_context()).data)

    def update(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class SensitiveDataAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        from api.serializers import SensitiveDataAccessLogSerializer
        return SensitiveDataAccessLogSerializer

    def get_queryset(self):
        from accounts.models import SensitiveDataAccessLog

        return SensitiveDataAccessLog.objects.select_related('user', 'employee').order_by('-accessed_at')


class DocumentAccessRuleViewSet(AuditedModelViewSet):
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        from api.serializers import DocumentAccessRuleSerializer
        return DocumentAccessRuleSerializer

    def get_queryset(self):
        from documents.models import DocumentAccessRule

        return DocumentAccessRule.objects.select_related('role').order_by('role__name', 'category')
