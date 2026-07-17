"""Survey HTTP adapters."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.mixins import AuditedModelViewSet
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import SurveyQuestionSerializer, SurveyResponseSerializer, SurveySerializer
from employees.models import Employee
from surveys.models import Survey, SurveyQuestion, SurveyResponse


class SurveyViewSet(AuditedModelViewSet):
    queryset = Survey.objects.all().order_by('-created_at')
    serializer_class = SurveySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'available', 'submit', 'results'):
            return [IsAuthenticated()]
        return [IsAdminOrManagerOrReadOnly()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.get_serializer(instance).data
        data['questions'] = SurveyQuestionSerializer(
            instance.questions.all().order_by('order'), many=True,
        ).data
        return Response(data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        from surveys.services import get_active_surveys

        qs = get_active_surveys()
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        from surveys.services import submit_survey_responses

        survey = self.get_object()
        answers = request.data.get('answers', [])

        employee = None
        if not survey.is_anonymous:
            try:
                employee = Employee.objects.get(email=request.user.email)
            except Employee.DoesNotExist:
                return Response({'detail': 'Employee profile required.'}, status=400)

        try:
            result = submit_survey_responses(
                survey=survey, respondent=employee, answers=answers,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        from surveys.services import build_survey_results

        survey = self.get_object()
        results = build_survey_results(survey)
        return Response({
            'survey': self.get_serializer(survey).data,
            'total_responders': results['total_responders'],
            'questions': results['questions'],
        })


class SurveyQuestionViewSet(AuditedModelViewSet):
    serializer_class = SurveyQuestionSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        qs = SurveyQuestion.objects.select_related('survey').order_by('survey', 'order')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs


class SurveyResponseViewSet(AuditedModelViewSet):
    serializer_class = SurveyResponseSerializer

    def get_queryset(self):
        qs = SurveyResponse.objects.select_related('survey', 'question').order_by('-created_at')
        survey_id = self.request.query_params.get('survey')
        if survey_id:
            qs = qs.filter(survey_id=survey_id)
        return qs
