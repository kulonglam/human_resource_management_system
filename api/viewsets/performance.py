"""Performance domain HTTP adapters."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import (
    FeedbackRequestSerializer,
    FeedbackRoundSerializer,
    FeedbackSerializer,
    PerformanceAppraisalSerializer,
    PerformanceGoalSerializer,
)
from employees.models import Employee
from performance.models import Feedback, FeedbackRequest, FeedbackRound, PerformanceAppraisal, PerformanceGoal


class PerformanceGoalViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = PerformanceGoalSerializer

    def get_queryset(self):
        qs = PerformanceGoal.objects.select_related('employee').order_by('-created_at')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    def perform_create(self, serializer):
        serializer.save(set_by=self.request.user)


class PerformanceAppraisalViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = PerformanceAppraisalSerializer

    def get_queryset(self):
        qs = PerformanceAppraisal.objects.select_related('employee').order_by('-appraisal_period_end')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def submit(self, request, pk=None):
        from performance.services import submit_appraisal

        appraisal = self.get_object()
        submit_appraisal(
            appraisal,
            submitted_by_name=request.user.get_full_name() or request.user.username,
        )
        log_action(
            request, 'update', 'PerformanceAppraisal', appraisal.id, str(appraisal),
            'Appraisal submitted for review',
        )
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        from performance.services import approve_appraisal

        appraisal = self.get_object()
        approve_appraisal(appraisal)
        log_action(
            request, 'approve', 'PerformanceAppraisal', appraisal.id, str(appraisal),
            'Appraisal approved',
        )
        return Response(PerformanceAppraisalSerializer(appraisal).data)


class FeedbackRoundViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = FeedbackRoundSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(FeedbackRound.objects.all().order_by('-created_at'))

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        reqs = instance.feedback_requests.select_related('recipient', 'feedback_giver').all()
        data['stats'] = {
            'total': reqs.count(),
            'submitted': reqs.filter(status='submitted').count(),
            'pending': reqs.filter(status='pending').count(),
        }
        data['requests'] = FeedbackRequestSerializer(
            reqs, many=True, context=self.get_serializer_context()
        ).data
        return Response(data)

    @action(detail=True, methods=['post'], url_path='create-requests')
    def create_requests(self, request, pk=None):
        from performance.services import create_feedback_round_requests

        round_obj = self.get_object()
        created = create_feedback_round_requests(
            round_obj=round_obj,
            items=request.data.get('requests', []),
        )
        return Response({'created': created})


class FeedbackRequestViewSet(AuditedModelViewSet):
    serializer_class = FeedbackRequestSerializer

    def get_queryset(self):
        qs = FeedbackRequest.objects.select_related(
            'recipient', 'feedback_giver', 'feedback_round'
        ).order_by('-created_at')
        if self.request.user.is_admin or self.request.user.is_manager:
            return qs
        return qs.filter(feedback_giver=self.request.user)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        qs = self.get_queryset().filter(feedback_giver=request.user)
        pending = qs.filter(status='pending').count()
        submitted = qs.filter(status='submitted').count()
        serializer = self.get_serializer(qs, many=True)
        return Response({
            'requests': serializer.data,
            'pending': pending,
            'submitted': submitted,
        })

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        from performance.services import submit_feedback_request

        feedback_request = self.get_object()
        try:
            feedback = submit_feedback_request(
                feedback_request=feedback_request,
                user=request.user,
                data=request.data,
            )
        except PermissionError:
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FeedbackSerializer(feedback).data)

    @action(detail=False, methods=['get'], url_path='employee-summary')
    def employee_summary(self, request):
        from django.shortcuts import get_object_or_404
        from performance.services import employee_feedback_summary

        employee_id = request.query_params.get('employee')
        round_id = request.query_params.get('round')
        if not employee_id:
            return Response({'detail': 'employee query param required.'}, status=400)

        employee = get_object_or_404(Employee, pk=employee_id)
        summary = employee_feedback_summary(employee=employee, round_id=round_id)
        return Response({
            'employee': summary['employee'],
            'requests': FeedbackRequestSerializer(
                summary['requests'], many=True, context=self.get_serializer_context(),
            ).data,
            'averages': summary['averages'],
            'response_count': summary['response_count'],
        })


class FeedbackViewSet(AuditedModelViewSet):
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer
