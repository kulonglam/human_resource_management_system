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
        login(request, user)
        log_action(request, 'login', 'CustomUser', user.id, user.username, 'User logged in')
        return Response(UserSerializer(user).data)


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
        return Response({'allow_registration': settings.ALLOW_PUBLIC_REGISTRATION})


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


class UserListView(generics.ListAPIView):
    permission_classes = [IsAdminOrManager]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(is_active=True).order_by('username')


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
