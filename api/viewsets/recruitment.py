"""Recruitment domain HTTP adapters."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from api.approval_integration import process_recruitment_decision
from api.mixins import AuditedModelViewSet
from api.notifications import notify_application_status
from api.permissions import IsAdminOrManager, IsAdminOrManagerOrReadOnly
from api.serializers import (
    ApplicationNoteSerializer,
    ApplicationScorecardSerializer,
    ApplicationScorecardWriteSerializer,
    ApplicationSerializer,
    CompleteOnboardingSerializer,
    HireOnboardingSerializer,
    HiringTeamMemberSerializer,
    InterviewSerializer,
    JobOfferCreateSerializer,
    JobOfferSerializer,
    JobPipelineStageSerializer,
    JobPostingSerializer,
    OfferTemplateSerializer,
    ScorecardCriterionSerializer,
)
from recruitment.models import (
    Application,
    ApplicationNote,
    ApplicationScorecard,
    HireOnboarding,
    HiringTeamMember,
    Interview,
    JobOffer,
    JobPipelineStage,
    JobPosting,
    OfferTemplate,
    ScorecardCriterion,
)
from recruitment.services import (
    complete_hire_onboarding,
    create_offer_from_template_data,
    move_application_to_stage,
    after_interview_created,
    approve_job_offer,
    send_job_offer,
    submit_job_offer,
    update_application_after_save,
)


class JobPostingViewSet(AuditedModelViewSet):
    queryset = JobPosting.objects.all().order_by('-posted_on')
    serializer_class = JobPostingSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class ApplicationViewSet(AuditedModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Application.objects.select_related('job').order_by('-applied_on')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs

    def perform_update(self, serializer):
        previous_status = serializer.instance.get_status_display()
        old_status = serializer.instance.status
        application = serializer.save()
        update_application_after_save(
            application=application,
            old_status=old_status,
            previous_status_label=previous_status,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        application = self.get_object()
        outcome = process_recruitment_decision(request, application, True, request.data.get('comment', ''))
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        application.refresh_from_db()
        if application.email and outcome['result'] in ('approved', 'advanced'):
            notify_application_status(application, application.get_status_display())
        return Response(ApplicationSerializer(application, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def reject(self, request, pk=None):
        application = self.get_object()
        outcome = process_recruitment_decision(
            request, application, False, request.data.get('reason', request.data.get('comment', '')),
        )
        if outcome['status'] == 403:
            return Response({'detail': outcome['detail']}, status=status.HTTP_403_FORBIDDEN)
        application.refresh_from_db()
        if application.email:
            notify_application_status(application, application.get_status_display())
        return Response(ApplicationSerializer(application, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def move_stage(self, request, pk=None):
        application = self.get_object()
        stage_id = request.data.get('stage_id')
        if not stage_id:
            return Response({'detail': 'stage_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        stage = JobPipelineStage.objects.filter(pk=stage_id, job=application.job).first()
        if not stage:
            return Response({'detail': 'Invalid stage for this job.'}, status=status.HTTP_400_BAD_REQUEST)
        application = move_application_to_stage(application=application, stage=stage)
        return Response(ApplicationSerializer(application, context={'request': request}).data)


class ApplicationNoteViewSet(AuditedModelViewSet):
    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ApplicationNote.objects.select_related('application', 'author')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class InterviewViewSet(AuditedModelViewSet):
    serializer_class = InterviewSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = Interview.objects.select_related('application', 'created_by')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    def perform_create(self, serializer):
        interview = serializer.save(created_by=self.request.user)
        after_interview_created(interview=interview)


class JobPipelineStageViewSet(AuditedModelViewSet):
    serializer_class = JobPipelineStageSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = JobPipelineStage.objects.select_related('job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class HiringTeamMemberViewSet(AuditedModelViewSet):
    serializer_class = HiringTeamMemberSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = HiringTeamMember.objects.select_related('user', 'job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class ScorecardCriterionViewSet(AuditedModelViewSet):
    serializer_class = ScorecardCriterionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = ScorecardCriterion.objects.select_related('job')
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs


class ApplicationScorecardViewSet(AuditedModelViewSet):
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ApplicationScorecardWriteSerializer
        return ApplicationScorecardSerializer

    def get_queryset(self):
        qs = ApplicationScorecard.objects.select_related('reviewer', 'application').prefetch_related('ratings__criterion')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs


class OfferTemplateViewSet(AuditedModelViewSet):
    queryset = OfferTemplate.objects.filter(is_active=True).order_by('name')
    serializer_class = OfferTemplateSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class JobOfferViewSet(AuditedModelViewSet):
    serializer_class = JobOfferSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = JobOffer.objects.select_related('application', 'template', 'created_by')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='from-template')
    def from_template(self, request):
        serializer = JobOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        offer = create_offer_from_template_data(
            template=data['template'],
            application=data['application'],
            created_by=request.user,
            salary=data['salary'],
            start_date=data['start_date'],
            currency=data.get('currency', 'UGX'),
            job_title=data.get('job_title') or data['application'].job.title,
            department=data.get('department') or data['application'].job.department,
        )
        return Response(JobOfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        offer = self.get_object()
        offer = submit_job_offer(offer)
        return Response(JobOfferSerializer(offer).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrManager])
    def approve(self, request, pk=None):
        offer = self.get_object()
        try:
            offer = approve_job_offer(offer)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(JobOfferSerializer(offer).data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        offer = self.get_object()
        try:
            offer = send_job_offer(offer)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(JobOfferSerializer(offer).data)


class HireOnboardingViewSet(AuditedModelViewSet):
    serializer_class = HireOnboardingSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    http_method_names = ['get', 'patch', 'head', 'options', 'post']

    def get_queryset(self):
        qs = HireOnboarding.objects.select_related('application', 'employee').order_by('-created_at')
        application_id = self.request.query_params.get('application')
        if application_id:
            qs = qs.filter(application_id=application_id)
        return qs

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        onboarding = self.get_object()
        if onboarding.status == 'completed':
            return Response({'detail': 'Onboarding already completed.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompleteOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            employee = complete_hire_onboarding(onboarding, request.user, serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        onboarding.refresh_from_db()
        return Response({
            'onboarding': HireOnboardingSerializer(onboarding).data,
            'employee_id': employee.id,
        })
