"""Performance appraisal and feedback use-cases."""

from django.utils import timezone


def submit_appraisal(appraisal, *, submitted_by_name):
    appraisal.status = 'submitted'
    appraisal.submitted_at = timezone.now()
    appraisal.save(update_fields=['status', 'submitted_at'])
    from api.notifications import notify_appraisal_submitted

    notify_appraisal_submitted(appraisal, submitted_by_name)
    return appraisal


def approve_appraisal(appraisal):
    appraisal.status = 'approved'
    appraisal.approved_at = timezone.now()
    appraisal.save(update_fields=['status', 'approved_at'])
    from api.notifications import notify_appraisal_approved

    notify_appraisal_approved(appraisal)
    return appraisal


def create_feedback_round_requests(*, round_obj, items):
    from performance.models import FeedbackRequest

    created = 0
    for item in items:
        _, was_created = FeedbackRequest.objects.get_or_create(
            feedback_round=round_obj,
            recipient_id=item['recipient'],
            feedback_giver_id=item['feedback_giver'],
            defaults={'giver_type': item.get('giver_type', 'peer')},
        )
        if was_created:
            created += 1
    return created


def submit_feedback_request(*, feedback_request, user, data):
    from performance.models import Feedback

    if feedback_request.feedback_giver != user:
        raise PermissionError('Not authorized.')
    if feedback_request.status == 'submitted':
        raise ValueError('Already submitted.')

    rating_fields = [
        'communication', 'leadership', 'teamwork',
        'reliability', 'initiative', 'problem_solving',
    ]
    defaults = {field: data.get(field) for field in rating_fields}
    defaults.update({
        'strengths': data.get('strengths', ''),
        'areas_for_improvement': data.get('areas_for_improvement', ''),
        'additional_comments': data.get('additional_comments', ''),
        'is_anonymous': data.get('is_anonymous', False),
    })
    feedback, _ = Feedback.objects.update_or_create(
        request=feedback_request,
        defaults=defaults,
    )
    feedback_request.status = 'submitted'
    feedback_request.submitted_at = timezone.now()
    feedback_request.save(update_fields=['status', 'submitted_at'])
    return feedback


def employee_feedback_summary(*, employee, round_id=None):
    from django.db.models import Avg

    from performance.models import Feedback, FeedbackRequest

    requests_qs = FeedbackRequest.objects.filter(
        recipient=employee, status='submitted',
    ).select_related('feedback_round', 'feedback_giver')
    if round_id:
        requests_qs = requests_qs.filter(feedback_round_id=round_id)

    feedbacks = Feedback.objects.filter(request__in=requests_qs)
    averages = {}
    for field in [
        'communication', 'leadership', 'teamwork',
        'reliability', 'initiative', 'problem_solving',
    ]:
        val = feedbacks.aggregate(v=Avg(field))['v']
        averages[field] = round(val, 2) if val is not None else None

    return {
        'employee': {'id': employee.id, 'full_name': employee.full_name},
        'requests': requests_qs,
        'averages': averages,
        'response_count': feedbacks.count(),
    }
