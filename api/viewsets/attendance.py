"""Attendance domain HTTP adapters."""
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import CanApproveAttendance, IsAdmin, IsAdminOrManagerOrReadOnly
from api.serializers import (
    AttendanceDeviceCreateSerializer,
    AttendanceDeviceSerializer,
    AttendanceSerializer,
    DevicePunchSerializer,
    OvertimeRecordSerializer,
    PublicHolidaySerializer,
    TimesheetSerializer,
)
from attendance.models import Attendance, AttendanceDevice, DevicePunch, OvertimeRecord, PublicHoliday, Timesheet
from attendance.services import (
    approve_attendance,
    approve_overtime,
    approve_timesheet,
    authenticate_attendance_device,
    create_attendance_device,
    finalize_attendance_record,
    import_attendance_csv,
    ingest_device_punch,
    reject_attendance,
    reject_overtime,
    submit_attendance,
    submit_timesheet,
    sync_offline_punches,
)
from employees.models import Employee


class AttendanceViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = Attendance.objects.select_related(
            'employee', 'approved_by', 'shift_assignment__shift',
        ).order_by('-date')
        qs = self.scope_to_accessible_employees(qs)
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        approval_status = self.request.query_params.get('approval_status')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if approval_status:
            qs = qs.filter(approval_status=approval_status)
        return qs

    def perform_create(self, serializer):
        attendance = serializer.save()
        finalize_attendance_record(attendance)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        attendance = self.get_object()
        try:
            attendance = submit_attendance(attendance)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        attendance = self.get_object()
        try:
            attendance = approve_attendance(attendance, approved_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request, 'approve', 'Attendance', attendance.id, str(attendance), 'Attendance approved')
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def reject(self, request, pk=None):
        attendance = self.get_object()
        try:
            attendance = reject_attendance(
                attendance,
                approved_by=request.user,
                reason=request.data.get('reason', attendance.notes),
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request, 'reject', 'Attendance', attendance.id, str(attendance), 'Attendance rejected')
        return Response(AttendanceSerializer(attendance, context={'request': request}).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser], permission_classes=[CanApproveAttendance])
    def import_csv(self, request):
        from api.uploads import validate_upload

        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': 'CSV file is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_upload(upload, kind='csv')
        except Exception as exc:
            detail = getattr(exc, 'detail', str(exc))
            return Response(detail if isinstance(detail, dict) else {'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        result = import_attendance_csv(upload)
        log_action(request, 'create', 'Attendance', None, 'Attendance import', f'Imported {result["created"]} created, {result["updated"]} updated')
        return Response(result)


class PublicHolidayViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(PublicHoliday.objects.all())


class TimesheetViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = TimesheetSerializer

    def get_queryset(self):
        qs = Timesheet.objects.select_related('employee', 'approved_by').order_by('-date')
        qs = self.scope_to_accessible_employees(qs)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        timesheet = self.get_object()
        try:
            timesheet = submit_timesheet(timesheet)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TimesheetSerializer(timesheet, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        timesheet = self.get_object()
        try:
            timesheet = approve_timesheet(timesheet, approved_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request, 'approve', 'Timesheet', timesheet.id, str(timesheet), 'Timesheet approved')
        return Response(TimesheetSerializer(timesheet, context={'request': request}).data)


class OvertimeRecordViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = OvertimeRecordSerializer

    def get_queryset(self):
        qs = OvertimeRecord.objects.select_related('employee', 'approved_by').order_by('-date')
        qs = self.scope_to_accessible_employees(qs)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def approve(self, request, pk=None):
        record = self.get_object()
        try:
            record = approve_overtime(record, approved_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request, 'approve', 'OvertimeRecord', record.id, str(record), 'Overtime approved')
        return Response(OvertimeRecordSerializer(record, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveAttendance])
    def reject(self, request, pk=None):
        record = self.get_object()
        try:
            record = reject_overtime(record, approved_by=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OvertimeRecordSerializer(record, context={'request': request}).data)


class AttendanceDeviceViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    """Admin management of biometric / device terminals."""

    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        return self.scope_to_organization(AttendanceDevice.objects.all().order_by('name'))

    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceDeviceCreateSerializer
        return AttendanceDeviceSerializer

    def create(self, request, *args, **kwargs):
        serializer = AttendanceDeviceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = getattr(request.user, 'organization', None)
        device, raw_token = create_attendance_device(
            organization=org,
            **serializer.validated_data,
        )
        log_action(request, 'create', 'AttendanceDevice', device.id, device.name, 'Device registered')
        data = AttendanceDeviceSerializer(device).data
        data['device_token'] = raw_token
        return Response(data, status=status.HTTP_201_CREATED)


class DevicePunchViewSet(AuditedModelViewSet):
    """Read-only punch log for ops / attendance admins."""

    serializer_class = DevicePunchSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        from django.db.models import Q

        qs = DevicePunch.objects.select_related('employee', 'device').order_by('-punched_at')
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id:
            qs = qs.filter(
                Q(employee__organization_id=org_id)
                | Q(device__organization_id=org_id),
            )
        return qs


class DevicePunchIngestView(APIView):
    """Hardware terminal punch ingest authenticated by device token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = (
            request.META.get('HTTP_X_DEVICE_TOKEN')
            or request.headers.get('X-Device-Token')
            or ''
        )
        device = authenticate_attendance_device(raw)
        if not device:
            return Response({'detail': 'Invalid device token.'}, status=status.HTTP_401_UNAUTHORIZED)

        badge_id = request.data.get('badge_id') or request.data.get('employee_number') or ''
        punched_at = request.data.get('punched_at')
        if punched_at:
            punched_at = parse_datetime(str(punched_at).replace('Z', '+00:00'))
        punch = ingest_device_punch(
            device=device,
            badge_id=badge_id,
            punched_at=punched_at,
            punch_type=request.data.get('punch_type', 'auto'),
            source='device',
            client_punch_id=request.data.get('client_punch_id', ''),
            raw_payload=request.data if isinstance(request.data, dict) else {},
        )
        return Response(DevicePunchSerializer(punch).data, status=status.HTTP_201_CREATED)


class MobilePunchView(APIView):
    """Authenticated mobile clock in/out (online)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            employee = Employee.objects.get(email=request.user.email, is_active=True)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee profile linked to your account.'}, status=400)

        punched_at = request.data.get('punched_at')
        if punched_at:
            punched_at = parse_datetime(str(punched_at).replace('Z', '+00:00'))
        punch = ingest_device_punch(
            employee=employee,
            badge_id=employee.device_badge_id or employee.employee_number,
            punched_at=punched_at,
            punch_type=request.data.get('punch_type', 'auto'),
            source='mobile',
            client_punch_id=request.data.get('client_punch_id', ''),
            raw_payload=request.data if isinstance(request.data, dict) else {},
        )
        return Response(DevicePunchSerializer(punch).data, status=status.HTTP_201_CREATED)


class MobilePunchSyncView(APIView):
    """Flush offline-queued punches from the mobile client."""

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            employee = Employee.objects.get(email=request.user.email, is_active=True)
        except Employee.DoesNotExist:
            return Response({'detail': 'No employee profile linked to your account.'}, status=400)
        results = sync_offline_punches(employee, request.data.get('punches') or [])
        return Response({'synced': len(results), 'results': results})
