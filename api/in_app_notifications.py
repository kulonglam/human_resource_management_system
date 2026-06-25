from accounts.models import CustomUser, Notification


def notify_users(users, title, message, category='system', link=''):
    created = []
    for user in users:
        if not user or not getattr(user, 'pk', None):
            continue
        created.append(Notification.objects.create(
            user=user,
            title=title,
            message=message,
            category=category,
            link=link,
        ))
    return created


def notify_user(user, title, message, category='system', link=''):
    if not user or not getattr(user, 'pk', None):
        return None
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        category=category,
        link=link,
    )


def get_hr_users():
    return CustomUser.objects.filter(role__name='admin', is_active=True)


def get_manager_users_for_employee(employee):
    if not employee or not employee.department_id:
        return CustomUser.objects.filter(role__name='manager', is_active=True)

    dept_employee_emails = employee.department.employees.filter(is_active=True).values_list('email', flat=True)
    return CustomUser.objects.filter(
        email__in=dept_employee_emails,
        role__name='manager',
        is_active=True,
    )
