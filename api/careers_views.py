from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from recruitment.models import Application, JobPosting

from api.serializers import ApplicationSerializer, PublicApplicationSerializer, PublicJobPostingSerializer
from .in_app_notifications import get_hr_users, notify_users


class PublicJobListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = timezone.now().date()
        jobs = JobPosting.objects.filter(is_open=True, deadline__gte=today).order_by('-posted_on')
        return Response(PublicJobPostingSerializer(jobs, many=True).data)


class PublicJobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        today = timezone.now().date()
        job = get_object_or_404(JobPosting, pk=job_id, is_open=True, deadline__gte=today)
        return Response(PublicJobPostingSerializer(job).data)


class PublicApplyView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, job_id):
        today = timezone.now().date()
        job = get_object_or_404(JobPosting, pk=job_id, is_open=True, deadline__gte=today)
        serializer = PublicApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save(job=job, source='careers_portal', status='received')
        notify_users(
            list(get_hr_users()),
            f'New application — {application.first_name} {application.last_name}',
            f'Applied for {job.title} via careers portal',
            'recruitment',
            f'/recruitment/applications/{application.id}',
        )
        return Response(
            ApplicationSerializer(application, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
