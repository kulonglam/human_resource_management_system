from accounts.models import AuditLog


def get_client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_action(
    request,
    action,
    model_name,
    object_id=None,
    object_description='',
    details='',
):
    user = None
    if request is not None and getattr(request, 'user', None) and request.user.is_authenticated:
        user = request.user

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_description=object_description,
        details=details,
        ip_address=get_client_ip(request),
    )
