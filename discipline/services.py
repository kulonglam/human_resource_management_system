"""Discipline appeal use-cases."""

from django.utils import timezone


def after_appeal_created(appeal):
    from api.notifications import notify_discipline_appeal_submitted

    notify_discipline_appeal_submitted(appeal)
    return appeal


def approve_discipline_appeal(appeal, *, review_notes=''):
    appeal.status = 'approved'
    appeal.review_date = timezone.now().date()
    appeal.review_notes = review_notes or appeal.review_notes
    appeal.save()
    from api.notifications import notify_discipline_appeal_decision

    notify_discipline_appeal_decision(appeal, 'approved')
    return appeal


def reject_discipline_appeal(appeal, *, review_notes=''):
    appeal.status = 'rejected'
    appeal.review_date = timezone.now().date()
    appeal.review_notes = review_notes or appeal.review_notes
    appeal.save()
    from api.notifications import notify_discipline_appeal_decision

    notify_discipline_appeal_decision(appeal, 'rejected')
    return appeal
