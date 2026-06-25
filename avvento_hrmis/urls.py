"""
URL configuration for avvento_hrmis project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from .error_views import permission_denied_view
from .spa_views import ReactAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]

_react_assets = settings.REACT_BUILD_DIR / 'assets'
if _react_assets.exists():
    urlpatterns.append(
        path('assets/<path:path>', serve, {'document_root': _react_assets}),
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^(?!api/|admin/|media/).*$', ReactAppView.as_view(), name='react-app'),
]

handler403 = permission_denied_view
