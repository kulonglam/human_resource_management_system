"""Survey submission and results use-cases."""

from django.db.models import Avg, Count
from django.utils import timezone

from surveys.models import Survey, SurveyResponse


def get_active_surveys(*, today=None):
    today = today or timezone.now().date()
    return Survey.objects.filter(
        status='active', start_date__lte=today, end_date__gte=today,
    ).order_by('-created_at')


def submit_survey_responses(*, survey, respondent, answers):
    if not answers:
        raise ValueError('No answers provided.')

    for ans in answers:
        question_id = ans.get('question_id')
        if not question_id:
            continue
        SurveyResponse.objects.create(
            survey=survey,
            respondent=respondent,
            question_id=question_id,
            response_text=ans.get('response_text', ''),
            response_rating=ans.get('response_rating'),
            response_selected=ans.get('response_selected', ''),
        )
    return {'detail': 'Survey submitted successfully.'}


def build_survey_results(survey):
    question_results = []
    for question in survey.questions.all().order_by('order'):
        responses = SurveyResponse.objects.filter(survey=survey, question=question)
        item = {
            'question_id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'total_responses': responses.count(),
        }
        if question.question_type == 'rating':
            item['average_rating'] = round(
                responses.aggregate(v=Avg('response_rating'))['v'] or 0, 2,
            )
            item['distribution'] = list(
                responses.values('response_rating').annotate(count=Count('id')),
            )
        elif question.question_type == 'text':
            item['text_responses'] = list(
                responses.values_list('response_text', flat=True)[:100],
            )
        else:
            item['selected_responses'] = list(
                responses.values_list('response_selected', flat=True)[:100],
            )
        question_results.append(item)

    unique_responders = SurveyResponse.objects.filter(survey=survey).values(
        'respondent',
    ).distinct().count()

    return {
        'total_responders': unique_responders,
        'questions': question_results,
    }
