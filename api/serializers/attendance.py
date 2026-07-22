"""Attendance domain serializers."""
from rest_framework import serializers

from attendance.models import (
    Attendance,
    AttendanceDevice,
    DevicePunch,
    OvertimeRecord,
    PublicHoliday,
    Timesheet,
)

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)
    shift_name = serializers.CharField(source='shift_assignment.shift.shift_name', read_only=True, default=None)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['approved_by', 'approved_at']



class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = '__all__'



class TimesheetSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = Timesheet
        fields = '__all__'
        read_only_fields = ['submitted_at', 'approved_by', 'approved_at', 'overtime_hours']

    def validate(self, attrs):
        from attendance.services import hours_worked

        clock_in = attrs.get('clock_in') or getattr(self.instance, 'clock_in', None)
        clock_out = attrs.get('clock_out') or getattr(self.instance, 'clock_out', None)
        if clock_in and clock_out:
            if clock_out <= clock_in:
                raise serializers.ValidationError({'clock_out': 'Clock-out must be after clock-in.'})
            if 'regular_hours' not in attrs:
                attrs['regular_hours'] = hours_worked(clock_in, clock_out)
        return attrs



class OvertimeRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, default=None)

    class Meta:
        model = OvertimeRecord
        fields = '__all__'
        read_only_fields = ['approved_by', 'approved_at', 'created_at']


class AttendanceDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceDevice
        fields = [
            'id', 'name', 'device_code', 'device_type', 'location', 'organization',
            'is_active', 'token_prefix', 'last_seen_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['token_prefix', 'last_seen_at', 'created_at', 'updated_at']


class AttendanceDeviceCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    device_code = serializers.SlugField(max_length=64)
    device_type = serializers.ChoiceField(choices=AttendanceDevice.DEVICE_TYPES, default='fingerprint')
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)


class DevicePunchSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, default=None)
    device_name = serializers.CharField(source='device.name', read_only=True, default=None)

    class Meta:
        model = DevicePunch
        fields = [
            'id', 'device', 'device_name', 'employee', 'employee_name', 'badge_id',
            'punched_at', 'punch_type', 'source', 'client_punch_id', 'applied',
            'error_message', 'attendance', 'created_at',
        ]
        read_only_fields = fields

