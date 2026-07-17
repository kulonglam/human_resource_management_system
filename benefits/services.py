"""Benefit enrollment use-cases."""


def after_enrollment_created(enrollment):
    if enrollment.status == 'pending':
        from api.notifications import notify_benefit_enrollment_submitted

        notify_benefit_enrollment_submitted(enrollment)
    return enrollment


def after_enrollment_updated(enrollment, *, previous_status):
    from api.notifications import notify_benefit_enrollment_decision

    if previous_status == 'pending' and enrollment.status == 'active':
        notify_benefit_enrollment_decision(enrollment, 'approved')
    elif previous_status == 'pending' and enrollment.status == 'terminated':
        notify_benefit_enrollment_decision(enrollment, 'rejected')
    return enrollment
