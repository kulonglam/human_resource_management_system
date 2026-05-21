"""
URL configuration for avvento_hrmis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from .error_views import permission_denied_view

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('departments/', include('departments.urls')),
    path('employees/', include('employees.urls')),
    path('kin/', include('kin.urls')),
    path('attendance/', include('attendance.urls')),
    path('leave/', include('leaves.urls')),
    path('recruitment/', include('recruitment.urls')),
    path('payroll/', include('payroll.urls')),
    path('', include('accounts.urls')),   # root → login/dashboard
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = permission_denied_view
