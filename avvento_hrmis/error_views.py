from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def permission_denied_view(request, exception=None):
    """Handle 403 Permission Denied errors."""
    return render(request, '403.html', status=403)


def page_not_found_view(request, exception=None):
    """Handle 404 Page Not Found errors."""
    return render(request, '404.html', status=404)


def server_error_view(request):
    """Handle 500 Server errors."""
    return render(request, '500.html', status=500)
