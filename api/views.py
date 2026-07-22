from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import login, logout

from accounts.models import CustomUser
from departments.models import Department
from employees.models import Employee
from leaves.models import Leave, LeaveBalance
from performance.models import PerformanceAppraisal, PerformanceGoal
from recruitment.models import JobPosting, Application
from training.models import (
    DevelopmentPlan,
    EmployeeCertification,
    TrainingCourse,
    TrainingRecord,
)
from attendance.models import Attendance

from .audit import log_action
from .dashboard_service import build_role_dashboard
from .mfa import (
    consume_pending_mfa_token,
    consume_setup_secret,
    create_pending_mfa_token,
    generate_mfa_secret,
    get_setup_secret,
    get_totp,
    store_setup_secret,
    verify_totp,
)
from .ops_monitoring import get_health_snapshot
from .permissions import IsAdmin, IsAdminOrManager
from .throttles import LoginRateThrottle, MFARateThrottle, PasswordResetRateThrottle
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
from accounts.security import (
    clear_failed_logins,
    is_login_locked,
    log_security_event,
    record_failed_login,
)


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        if username and is_login_locked(username):
            log_security_event('login_locked', username, request=request)
            return Response(
                {'detail': 'Account temporarily locked due to failed login attempts. Try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            if username:
                record_failed_login(username)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        clear_failed_logins(user.username)

        if user.mfa_enabled and user.mfa_secret:
            token = create_pending_mfa_token(user.id)
            return Response({'mfa_required': True, 'mfa_token': token})

        if settings.ENFORCE_MFA_FOR_ADMINS and user.is_admin and not user.mfa_enabled:
            login(request, user)
            log_action(request, 'login', 'CustomUser', user.id, user.username, 'Admin login (MFA setup pending)')
            return Response(UserSerializer(user).data)

        if settings.ENFORCE_MFA_FOR_MANAGERS and user.is_manager and not user.mfa_enabled:
            login(request, user)
            log_action(request, 'login', 'CustomUser', user.id, user.username, 'Manager login (MFA setup pending)')
            return Response(UserSerializer(user).data)

        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, 'User logged in')
        return Response(UserSerializer(user).data)


class MFAVerifyView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [MFARateThrottle]

    def post(self, request):
        token = request.data.get('mfa_token', '')
        code = request.data.get('code', '')
        user_id = consume_pending_mfa_token(token)
        if not user_id:
            return Response({'detail': 'Invalid or expired MFA session.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(pk=user_id, is_active=True)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_totp(user.mfa_secret, code):
            log_security_event('mfa_failed', user.username, user=user, request=request)
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, 'MFA verified login')
        return Response(UserSerializer(user).data)


class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.mfa_enabled:
            return Response({'detail': 'MFA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)
        secret = generate_mfa_secret()
        store_setup_secret(user.id, secret)
        totp = get_totp(secret)
        return Response({
            'secret': secret,
            'provisioning_uri': totp.provisioning_uri(name=user.email, issuer_name='FCA HRMIS'),
        })

    def post(self, request):
        code = request.data.get('code', '')
        secret = get_setup_secret(request.user.id)
        if not secret or not verify_totp(secret, code):
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        consume_setup_secret(request.user.id)
        request.user.mfa_secret = secret
        request.user.mfa_enabled = True
        request.user.save(update_fields=['mfa_secret', 'mfa_enabled'])
        log_action(request, 'update', 'CustomUser', request.user.id, request.user.username, 'MFA enabled')
        return Response({'detail': 'MFA enabled successfully.', 'user': UserSerializer(request.user).data})


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payload = get_health_snapshot()
        payload.pop('error', None)
        http_status = (
            status.HTTP_200_OK if payload['status'] == 'ok' else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(payload, status=http_status)


class LogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            log_action(
                request, 'logout', 'CustomUser', request.user.id,
                request.user.username, 'User logged out',
            )
        logout(request)
        return Response({'detail': 'Logged out.'})


class AuthConfigView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'allow_registration': settings.ALLOW_PUBLIC_REGISTRATION,
            'enforce_mfa_for_admins': settings.ENFORCE_MFA_FOR_ADMINS,
            'enforce_mfa_for_managers': settings.ENFORCE_MFA_FOR_MANAGERS,
            'api_version': '1.2.0',
        })


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def get_permissions(self):
        if settings.ALLOW_PUBLIC_REGISTRATION:
            return [AllowAny()]
        return [IsAdmin()]

    def create(self, request, *args, **kwargs):
        if not settings.ALLOW_PUBLIC_REGISTRATION and not (
            request.user.is_authenticated and getattr(request.user, 'is_admin', False)
        ):
            return Response(
                {'detail': 'Registration is disabled.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(request, 'create', 'CustomUser', user.id, user.username, 'User registered')
        if settings.ALLOW_PUBLIC_REGISTRATION:
            login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PasswordResetRequestView(APIView):
    """Send a password-reset link. Always returns success to avoid account enumeration."""

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        from .notifications import notify_password_reset

        email = (request.data.get('email') or '').strip()
        username = (request.data.get('username') or '').strip()

        user = None
        if email:
            user = CustomUser.objects.filter(email__iexact=email, is_active=True).first()
        elif username:
            user = CustomUser.objects.filter(username__iexact=username, is_active=True).first()

        if user and user.email:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            base = settings.FRONTEND_BASE_URL.rstrip('/')
            reset_url = f'{base}/reset-password?uid={uid}&token={token}'
            notify_password_reset(user, reset_url)
            log_security_event('password_reset_requested', user.username, request=request)

        return Response({
            'detail': (
                'If an account matches that email or username, '
                'password reset instructions have been sent.'
            ),
        })


class PasswordResetConfirmView(APIView):
    """Set a new password using a valid uid + token from the reset email."""

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_str
        from django.utils.http import urlsafe_base64_decode
        from rest_framework import serializers as drf_serializers

        from api.validation import validate_user_password

        uid = (request.data.get('uid') or '').strip()
        token = (request.data.get('token') or '').strip()
        password = request.data.get('password') or ''
        password_confirm = request.data.get('password_confirm') or ''

        if not uid or not token:
            return Response(
                {'detail': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if password != password_confirm:
            return Response(
                {'password_confirm': ['Passwords do not match.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id, is_active=True)
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {'detail': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'detail': 'Invalid or expired reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_user_password(password, user=user)
        except drf_serializers.ValidationError as exc:
            return Response({'password': exc.detail}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save(update_fields=['password'])
        clear_failed_logins(user.username)
        log_security_event('password_reset_completed', user.username, request=request)
        log_action(
            request, 'update', 'CustomUser', user.id, user.username, 'Password reset completed',
        )
        return Response({'detail': 'Password updated. You can sign in with your new password.'})


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        current_year = timezone.now().year

        data = {
            'total_employees': Employee.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.count(),
            'pending_leaves': Leave.objects.filter(status='pending').count(),
            'open_jobs': JobPosting.objects.filter(is_open=True).count(),
            'total_goals': PerformanceGoal.objects.count(),
            'active_goals': PerformanceGoal.objects.filter(status='in_progress').count(),
            'total_appraisals': PerformanceAppraisal.objects.count(),
            'active_courses': TrainingCourse.objects.filter(status='active').count(),
            'upcoming_courses': TrainingCourse.objects.filter(status='planned').count(),
            'total_employees_trained': TrainingRecord.objects.filter(
                status='completed'
            ).values('employee').distinct().count(),
            'expiring_certifications': EmployeeCertification.objects.filter(
                expiry_date__lte=timezone.now() + timedelta(days=30),
                expiry_date__gte=timezone.now(),
            ).count(),
            'active_development_plans': DevelopmentPlan.objects.filter(status='active').count(),
            'user_leave_balances': [],
            'dept_leave_summary': None,
            'all_leave_summary': None,
        }

        try:
            employee = Employee.objects.get(email=user.email)
            balances = LeaveBalance.objects.filter(employee=employee, year=current_year)
            data['user_leave_balances'] = [
                {
                    'leave_type': b.leave_type,
                    'leave_type_display': b.get_leave_type_display(),
                    'used_days': float(b.used_days),
                    'pending_days': float(b.pending_days),
                    'available_days': float(b.available_days),
                    'total_days': b.total_days,
                }
                for b in balances
            ]

            if user.is_manager and employee.department:
                dept_employees = Employee.objects.filter(
                    department=employee.department, is_active=True
                )
                dept_balances = LeaveBalance.objects.filter(
                    employee__in=dept_employees, year=current_year
                )
                data['dept_leave_summary'] = {
                    'total_used': sum(b.used_days for b in dept_balances),
                    'total_pending': sum(b.pending_days for b in dept_balances),
                    'total_available': sum(b.available_days for b in dept_balances),
                    'employee_count': dept_employees.count(),
                }

            if user.is_admin:
                all_balances = LeaveBalance.objects.filter(year=current_year)
                data['all_leave_summary'] = {
                    'total_used': sum(b.used_days for b in all_balances),
                    'total_pending': sum(b.pending_days for b in all_balances),
                    'total_available': sum(b.available_days for b in all_balances),
                    'total_allocated': sum(b.total_days for b in all_balances),
                }
        except Employee.DoesNotExist:
            pass

        data.update(build_role_dashboard(user, data))
        return Response(data)


class ReportsAnalyticsView(APIView):
    """Deprecated: use GET /api/v1/reports/filters/ (includes ``overview``)."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        from .report_views import build_reports_overview

        return Response(build_reports_overview())
