from django.http import HttpResponse
from django.views.decorators.csrf import requires_csrf_token


def _error_page(title, message, status):
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:32rem;margin:4rem auto;padding:0 1rem;color:#004924}}
a{{color:#004924}}</style></head>
<body><h1>{title}</h1><p>{message}</p><p><a href="/">Return to FCA HRMIS</a></p></body></html>"""
    return HttpResponse(html, status=status, content_type='text/html')


@requires_csrf_token
def permission_denied_view(request, exception=None):
    return _error_page('403 Forbidden', 'You do not have permission to access this resource.', 403)


def page_not_found_view(request, exception=None):
    return _error_page('404 Not Found', 'The page you requested could not be found.', 404)


def server_error_view(request):
    return _error_page('500 Server Error', 'Something went wrong. Please try again later.', 500)
