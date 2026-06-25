from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import login, logout

from accounts.models import CustomUser, Role
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
from .permissions import IsAdmin, IsAdminOrManager
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserSerializer,
)


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if settings.ENFORCE_MFA_FOR_ADMINS and user.is_admin:
            if user.mfa_enabled and user.mfa_secret:
                token = create_pending_mfa_token(user.id)
                return Response({
                    'mfa_required': True,
                    'mfa_token': token,
                })
            login(request, user)
            log_action(request, 'login', 'CustomUser', user.id, user.username, 'Admin login (MFA setup pending)')
            return Response(UserSerializer(user).data)

        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, 'User logged in')
        return Response(UserSerializer(user).data)


class MFAVerifyView(APIView):
    permission_classes = [AllowAny]

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
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, 'Admin login with MFA')
        return Response(UserSerializer(user).data)


class MFASetupView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

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
        db_ok = True
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_ok = False

        payload = {
            'status': 'ok' if db_ok else 'degraded',
            'database': 'ok' if db_ok else 'unavailable',
            'version': '1.0.0',
        }
        http_status = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
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


class RoleListView(generics.ListAPIView):
    serializer_class = RoleSerializer

    def get_permissions(self):
        from django.conf import settings
        if settings.ALLOW_PUBLIC_REGISTRATION:
            return [AllowAny()]
        return [IsAdmin()]

    def get_queryset(self):
        return Role.objects.all()


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
    def get(self, request):
        today = timezone.now().date()
        return Response({
            'total_employees': Employee.objects.filter(is_active=True).count(),
            'new_joiners': Employee.objects.filter(
                date_joined__gte=today - timedelta(days=30), is_active=True
            ).count(),
            'present_today': Attendance.objects.filter(date=today, status='present').count(),
            'absent_today': Attendance.objects.filter(date=today, status='absent').count(),
            'late_today': Attendance.objects.filter(date=today, status='late').count(),
            'pending_leaves': Leave.objects.filter(status='pending').count(),
            'leaves_used_this_year': Leave.objects.filter(
                status='approved', start_date__year=today.year
            ).count(),
            'open_positions': JobPosting.objects.filter(is_open=True).count(),
            'pending_applications': Application.objects.filter(status='received').count(),
            'active_goals': PerformanceGoal.objects.filter(status='in_progress').count(),
            'appraisals_due': PerformanceAppraisal.objects.filter(
                status__in=['draft', 'submitted'],
                appraisal_period_end__lte=today,
            ).count(),
        })
