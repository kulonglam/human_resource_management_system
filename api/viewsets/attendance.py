"""Attendance domain HTTP adapters."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from api.audit import log_action
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
from api.permissions import CanApproveAttendance, IsAdminOrManagerOrReadOnly
from api.serializers import (
    AttendanceSerializer,
    OvertimeRecordSerializer,
    PublicHolidaySerializer,
    TimesheetSerializer,
)
from attendance.models import Attendance, OvertimeRecord, PublicHoliday, Timesheet
from attendance.services import (
    approve_attendance,
    approve_overtime,
    approve_timesheet,
    finalize_attendance_record,
    import_attendance_csv,
    reject_attendance,
    reject_overtime,
    submit_attendance,
    submit_timesheet,
)


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


class PublicHolidayViewSet(AuditedModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


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
