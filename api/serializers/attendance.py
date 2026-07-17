"""Attendance domain serializers."""
from rest_framework import serializers

from attendance.models import Attendance, OvertimeRecord, PublicHoliday, Timesheet

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

