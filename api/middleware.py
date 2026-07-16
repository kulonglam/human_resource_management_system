"""Request tracing, API deprecation headers, and basic SLO counters."""

import time
import uuid
from threading import local

from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

_request_local = local()

# Paths that still work but should be migrated by API consumers
DEPRECATED_PATHS = {
    '/api/v1/reports/analytics/': {
        'successor': '/api/v1/reports/filters/',
        'sunset': 'Thu, 31 Dec 2026 23:59:59 GMT',
    },
}


def get_request_id():
    return getattr(_request_local, 'request_id', None)


class RequestIDMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request_id = request.META.get('HTTP_X_REQUEST_ID') or str(uuid.uuid4())
        request.request_id = request_id
        _request_local.request_id = request_id
        request._slo_started = time.monotonic()

    def process_response(self, request, response):
        request_id = getattr(request, 'request_id', None)
        if request_id:
            response['X-Request-ID'] = request_id

        started = getattr(request, '_slo_started', None)
        if started is not None and request.path.startswith('/api/'):
            elapsed_ms = (time.monotonic() - started) * 1000
            response['X-Response-Time-Ms'] = f'{elapsed_ms:.1f}'
            self._record_slo(request.path, response.status_code, elapsed_ms)

        return response

    def _record_slo(self, path, status_code, elapsed_ms):
        hour_key = time.strftime('%Y%m%d%H')
        requests_key = f'slo:requests:{hour_key}'
        errors_key = f'slo:errors:{hour_key}'
        latency_key = f'slo:latency_ms:{hour_key}'
        cache.add(requests_key, 0, 60 * 60 * 26)
        cache.add(errors_key, 0, 60 * 60 * 26)
        cache.add(latency_key, 0.0, 60 * 60 * 26)
        try:
            cache.incr(requests_key)
            if status_code >= 500:
                cache.incr(errors_key)
            # Approximate sum of latency for average computation
            current = cache.get(latency_key) or 0.0
            cache.set(latency_key, float(current) + float(elapsed_ms), 60 * 60 * 26)
        except Exception:
            pass


class DeprecationMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        meta = DEPRECATED_PATHS.get(request.path)
        if meta:
            response['Deprecation'] = 'true'
            response['Sunset'] = meta['sunset']
            response['Link'] = f'<{meta["successor"]}>; rel="successor-version"'
            response['X-API-Deprecation-Info'] = (
                f'This endpoint is deprecated. Prefer {meta["successor"]} before {meta["sunset"]}.'
            )
        response.setdefault('X-API-Version', '1.2.0')
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        from django.conf import settings

        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', '')
        if csp and 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = csp
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'same-origin')
        response.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        return response


class SessionIdleTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        from django.conf import settings
        from django.contrib.auth import logout
        from django.utils import timezone

        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return None
        timeout = int(getattr(settings, 'SESSION_IDLE_TIMEOUT_SECONDS', 0) or 0)
        if timeout <= 0:
            return None
        now = timezone.now().timestamp()
        last = request.session.get('_last_activity_ts')
        if last and (now - float(last)) > timeout:
            logout(request)
            request.session.flush()
            return None
        request.session['_last_activity_ts'] = now
        return None
