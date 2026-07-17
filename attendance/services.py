"""Attendance, timesheet, and overtime helpers."""

from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from shifts.models import ShiftAssignment


def _time_to_minutes(value):
    if not value:
        return None
    return value.hour * 60 + value.minute


def hours_worked(time_in, time_out):
    start = _time_to_minutes(time_in)
    end = _time_to_minutes(time_out)
    if start is None or end is None or end <= start:
        return 0.0
    return round((end - start) / 60, 2)


def match_shift_for_date(employee, day):
    return (
        ShiftAssignment.objects.filter(
            employee=employee,
            status='active',
            start_date__lte=day,
        )
        .filter(Q(end_date__gte=day) | Q(end_date__isnull=True))
        .select_related('shift')
        .order_by('-start_date')
        .first()
    )


def calculate_overtime_hours(regular_hours, expected_hours):
    overtime = float(regular_hours) - float(expected_hours)
    return round(max(overtime, 0), 2)


def derive_attendance_status(attendance):
    """Infer attendance status from clock times and assigned shift."""
    assignment = match_shift_for_date(attendance.employee, attendance.date)
    if not attendance.time_in:
        return 'absent'

    if assignment and assignment.shift:
        shift_start = _time_to_minutes(assignment.shift.start_time)
        actual_in = _time_to_minutes(attendance.time_in)
        if shift_start is not None and actual_in is not None and actual_in > shift_start + 15:
            return 'late'

    worked = hours_worked(attendance.time_in, attendance.time_out)
    if assignment and assignment.shift and worked < float(assignment.shift.working_hours) / 2:
        return 'half_day'
    return 'present'


def sync_timesheet_to_attendance(timesheet):
    from django.db import IntegrityError

    from attendance.models import Attendance

    try:
        attendance = Attendance.objects.select_for_update().get(
            employee=timesheet.employee,
            date=timesheet.date,
        )
    except Attendance.DoesNotExist:
        try:
            attendance = Attendance.objects.create(
                employee=timesheet.employee,
                date=timesheet.date,
                approval_status='draft',
                source='timesheet',
            )
        except IntegrityError:
            attendance = Attendance.objects.select_for_update().get(
                employee=timesheet.employee,
                date=timesheet.date,
            )

    assignment = match_shift_for_date(timesheet.employee, timesheet.date)
    expected = float(assignment.shift.working_hours) if assignment and assignment.shift else 8.0
    attendance.time_in = timesheet.clock_in
    attendance.time_out = timesheet.clock_out
    attendance.status = derive_attendance_status(attendance)
    attendance.shift_assignment = assignment
    attendance.notes = timesheet.notes or attendance.notes
    attendance.source = 'timesheet'
    attendance.save()

    timesheet.overtime_hours = calculate_overtime_hours(timesheet.regular_hours, expected)
    timesheet.save(update_fields=['overtime_hours'])
    return attendance


def import_attendance_csv(file_obj):
    """Parse CSV with columns: employee_number,date,time_in,time_out,status."""
    import csv
    from datetime import datetime

    from attendance.models import Attendance
    from employees.models import Employee

    decoded = file_obj.read().decode('utf-8-sig').splitlines()
    reader = csv.DictReader(decoded)
    created = 0
    updated = 0
    errors = []

    for line_no, row in enumerate(reader, start=2):
        employee_number = (row.get('employee_number') or row.get('employee') or '').strip()
        date_raw = (row.get('date') or '').strip()
        if not employee_number or not date_raw:
            errors.append({'line': line_no, 'error': 'employee_number and date are required'})
            continue
        try:
            employee = Employee.objects.get(employee_number=employee_number)
            day = datetime.strptime(date_raw, '%Y-%m-%d').date()
        except Employee.DoesNotExist:
            errors.append({'line': line_no, 'error': f'Unknown employee {employee_number}'})
            continue
        except ValueError:
            errors.append({'line': line_no, 'error': f'Invalid date {date_raw}'})
            continue

        defaults = {
            'source': 'import',
            'approval_status': 'draft',
            'status': (row.get('status') or 'present').strip() or 'present',
            'notes': (row.get('notes') or '').strip(),
        }
        for field in ('time_in', 'time_out'):
            raw = (row.get(field) or '').strip()
            if raw:
                defaults[field] = datetime.strptime(raw, '%H:%M').time()

        with transaction.atomic():
            record, was_created = Attendance.objects.update_or_create(
                employee=employee,
                date=day,
                defaults=defaults,
            )
        if was_created:
            created += 1
        else:
            updated += 1

    return {'created': created, 'updated': updated, 'errors': errors}


def finalize_attendance_record(attendance):
    """Match shift assignment and derive status after attendance is created."""
    assignment = match_shift_for_date(attendance.employee, attendance.date)
    if assignment:
        attendance.shift_assignment = assignment
    if attendance.time_in or attendance.time_out:
        attendance.status = derive_attendance_status(attendance)
    attendance.save()
    return attendance


def submit_attendance(attendance):
    from attendance.models import Attendance

    with transaction.atomic():
        attendance = Attendance.objects.select_for_update().get(pk=attendance.pk)
        if attendance.approval_status not in ('draft', 'rejected'):
            raise ValueError('Attendance is not in a submittable state.')
        attendance.approval_status = 'submitted'
        attendance.save(update_fields=['approval_status'])
    return attendance


def approve_attendance(attendance, *, approved_by):
    from attendance.models import Attendance

    with transaction.atomic():
        attendance = Attendance.objects.select_for_update().get(pk=attendance.pk)
        if attendance.approval_status != 'submitted':
            raise ValueError('Only submitted attendance can be approved.')
        attendance.approval_status = 'approved'
        attendance.approved_by = approved_by
        attendance.approved_at = timezone.now()
        attendance.save()
    return attendance


def reject_attendance(attendance, *, approved_by, reason=''):
    from attendance.models import Attendance

    with transaction.atomic():
        attendance = Attendance.objects.select_for_update().get(pk=attendance.pk)
        if attendance.approval_status != 'submitted':
            raise ValueError('Only submitted attendance can be rejected.')
        attendance.approval_status = 'rejected'
        attendance.approved_by = approved_by
        attendance.approved_at = timezone.now()
        attendance.notes = reason or attendance.notes
        attendance.save()
    return attendance


def submit_timesheet(timesheet):
    from attendance.models import Timesheet

    with transaction.atomic():
        timesheet = Timesheet.objects.select_for_update().get(pk=timesheet.pk)
        if timesheet.status not in ('draft', 'rejected'):
            raise ValueError('Timesheet is not in a submittable state.')
        timesheet.status = 'submitted'
        timesheet.submitted_at = timezone.now()
        timesheet.save()
    return timesheet


def approve_timesheet(timesheet, *, approved_by):
    from attendance.models import Timesheet

    with transaction.atomic():
        timesheet = Timesheet.objects.select_for_update().select_related('employee').get(
            pk=timesheet.pk,
        )
        if timesheet.status != 'submitted':
            raise ValueError('Only submitted timesheets can be approved.')
        timesheet.status = 'approved'
        timesheet.approved_by = approved_by
        timesheet.approved_at = timezone.now()
        timesheet.save()
        sync_timesheet_to_attendance(timesheet)
    return timesheet


def approve_overtime(record, *, approved_by):
    from attendance.models import OvertimeRecord

    with transaction.atomic():
        record = OvertimeRecord.objects.select_for_update().get(pk=record.pk)
        if record.status != 'pending':
            raise ValueError('Overtime record is not pending.')
        record.status = 'approved'
        record.approved_by = approved_by
        record.approved_at = timezone.now()
        record.save()
    return record


def reject_overtime(record, *, approved_by):
    from attendance.models import OvertimeRecord

    with transaction.atomic():
        record = OvertimeRecord.objects.select_for_update().get(pk=record.pk)
        if record.status != 'pending':
            raise ValueError('Overtime record is not pending.')
        record.status = 'rejected'
        record.approved_by = approved_by
        record.approved_at = timezone.now()
        record.save()
    return record


def document_expiry_reminders():
    from documents.models import HRDocument
    from accounts.models import Notification, CustomUser

    today = timezone.now().date()
    soon = today + timedelta(days=30)
    expiring = HRDocument.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lte=soon,
        expires_at__gte=today,
    )
    admins = CustomUser.objects.filter(role__name='admin', is_active=True)
    created = 0
    for document in expiring:
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title=f'Document expiring: {document.title}',
                message=f'Expires on {document.expires_at}.',
                category='document',
                link='/documents',
            )
            created += 1
    return {'expiring_documents': expiring.count(), 'notifications': created}
