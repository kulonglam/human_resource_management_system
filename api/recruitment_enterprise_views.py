from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recruitment.models import Application, Interview, JobOffer
from recruitment.services import generate_interview_ics

from .permissions import IsAdminOrManager


class InterviewCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        interview = get_object_or_404(
            Interview.objects.select_related('application__job'),
            pk=interview_id,
        )
        ics = generate_interview_ics(interview)
        response = HttpResponse(ics, content_type='text/calendar; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="interview-{interview_id}.ics"'
        return response


class RecruitmentEEOReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        apps = Application.objects.exclude(
            eeo_gender='',
            eeo_ethnicity='',
            eeo_veteran_status='',
            eeo_disability_status='',
        )
        job_id = request.query_params.get('job')
        if job_id:
            apps = apps.filter(job_id=job_id)

        def breakdown(field):
            return list(
                apps.exclude(**{field: ''})
                .values(field)
                .annotate(count=Count('id'))
                .order_by(field)
            )

        return Response({
            'total_with_eeo_data': apps.count(),
            'gender': breakdown('eeo_gender'),
            'ethnicity': breakdown('eeo_ethnicity'),
            'veteran_status': breakdown('eeo_veteran_status'),
            'disability_status': breakdown('eeo_disability_status'),
            'disclaimer': 'Voluntary self-identification data. Use only for compliance reporting.',
        })


class PublicOfferDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, offer_id):
        offer = get_object_or_404(
            JobOffer.objects.select_related('application'),
            pk=offer_id,
            status__in=['sent', 'accepted', 'declined'],
        )
        return Response({
            'id': offer.id,
            'candidate_name': f'{offer.application.first_name} {offer.application.last_name}',
            'job_title': offer.job_title,
            'department': offer.department,
            'salary': str(offer.salary),
            'currency': offer.currency,
            'start_date': offer.start_date,
            'body': offer.body,
            'status': offer.status,
            'signed_at': offer.signed_at,
            'signer_name': offer.signer_name,
        })


class PublicOfferSignView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, offer_id):
        offer = get_object_or_404(JobOffer, pk=offer_id, status='sent')
        signer_name = (request.data.get('signer_name') or '').strip()
        accept = request.data.get('accept', True)
        if not signer_name:
            return Response({'detail': 'Signer name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        client_ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

        offer.signer_name = signer_name
        offer.signer_ip = client_ip
        offer.signed_at = timezone.now()
        offer.status = 'accepted' if accept else 'declined'
        offer.save(update_fields=['signer_name', 'signer_ip', 'signed_at', 'status'])

        if accept:
            from recruitment.services import create_hire_onboarding, sync_application_stage

            application = offer.application
            stage = application.job.pipeline_stages.filter(stage_type='hired').first()
            if stage:
                sync_application_stage(application, stage)
            else:
                application.status = 'hired'
                application.hired_at = timezone.now()
                application.save(update_fields=['status', 'hired_at'])
            create_hire_onboarding(
                application,
                start_date=offer.start_date,
                salary=offer.salary,
                job_title=offer.job_title,
            )

        return Response({'status': offer.status, 'signed_at': offer.signed_at})
