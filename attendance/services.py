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


def create_attendance_device(*, name, device_code, device_type='fingerprint', location='', organization=None):
    """Register a terminal and return (device, raw_token). Token shown once."""
    import hashlib
    import secrets

    from attendance.models import AttendanceDevice

    raw = secrets.token_urlsafe(32)
    prefix = raw[:8]
    device = AttendanceDevice.objects.create(
        name=name,
        device_code=device_code,
        device_type=device_type,
        location=location or '',
        organization=organization,
        token_prefix=prefix,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
    )
    return device, raw


def authenticate_attendance_device(raw_token):
    import hashlib

    from attendance.models import AttendanceDevice

    if not raw_token or len(raw_token) < 12:
        return None
    prefix = raw_token[:8]
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        device = AttendanceDevice.objects.get(
            token_prefix=prefix, token_hash=digest, is_active=True,
        )
    except AttendanceDevice.DoesNotExist:
        return None
    AttendanceDevice.objects.filter(pk=device.pk).update(last_seen_at=timezone.now())
    return device


def resolve_employee_for_badge(badge_id, *, organization_id=None):
    from employees.models import Employee

    badge_id = (badge_id or '').strip()
    if not badge_id:
        return None
    qs = Employee.objects.filter(is_active=True).filter(
        Q(device_badge_id__iexact=badge_id) | Q(employee_number__iexact=badge_id),
    )
    if organization_id:
        qs = qs.filter(organization_id=organization_id)
    return qs.first()


def apply_punch_to_attendance(employee, punched_at, *, punch_type='auto', source='device'):
    """Upsert daily Attendance from a punch timestamp."""
    from attendance.models import Attendance

    day = timezone.localtime(punched_at).date()
    punch_time = timezone.localtime(punched_at).time().replace(microsecond=0)

    with transaction.atomic():
        attendance, _ = Attendance.objects.select_for_update().get_or_create(
            employee=employee,
            date=day,
            defaults={
                'source': source,
                'approval_status': 'draft',
                'status': 'present',
            },
        )
        if punch_type == 'out' or (punch_type == 'auto' and attendance.time_in and not attendance.time_out):
            attendance.time_out = punch_time
        else:
            if not attendance.time_in or punch_type == 'in':
                attendance.time_in = punch_time
            elif punch_type == 'auto':
                attendance.time_out = punch_time
        attendance.source = source
        assignment = match_shift_for_date(employee, day)
        if assignment:
            attendance.shift_assignment = assignment
        attendance.status = derive_attendance_status(attendance)
        attendance.save()
    return attendance


def ingest_device_punch(
    *,
    device=None,
    employee=None,
    badge_id='',
    punched_at=None,
    punch_type='auto',
    source='device',
    client_punch_id='',
    raw_payload=None,
):
    """Record a device/mobile punch and apply it to Attendance when possible."""
    from attendance.models import DevicePunch

    punched_at = punched_at or timezone.now()
    if timezone.is_naive(punched_at):
        punched_at = timezone.make_aware(punched_at)

    if client_punch_id:
        existing = DevicePunch.objects.filter(client_punch_id=client_punch_id).first()
        if existing:
            return existing

    if employee is None:
        org_id = getattr(device, 'organization_id', None) if device else None
        employee = resolve_employee_for_badge(badge_id, organization_id=org_id)

    punch = DevicePunch.objects.create(
        device=device,
        employee=employee,
        badge_id=(badge_id or getattr(employee, 'device_badge_id', '') or '')[:64],
        punched_at=punched_at,
        punch_type=punch_type,
        source=source,
        client_punch_id=client_punch_id or '',
        raw_payload=raw_payload or {},
    )
    if not employee:
        punch.error_message = 'No employee matched for badge/employee number.'
        punch.save(update_fields=['error_message'])
        return punch

    attendance = apply_punch_to_attendance(
        employee, punched_at, punch_type=punch_type, source=source,
    )
    punch.attendance = attendance
    punch.applied = True
    punch.save(update_fields=['attendance', 'applied'])
    return punch


def sync_offline_punches(employee, punches):
    """Apply a list of offline mobile punches for one employee."""
    results = []
    for item in punches or []:
        punched_at = item.get('punched_at')
        if isinstance(punched_at, str):
            punched_at = datetime.fromisoformat(punched_at.replace('Z', '+00:00'))
        punch = ingest_device_punch(
            employee=employee,
            badge_id=employee.device_badge_id or employee.employee_number,
            punched_at=punched_at,
            punch_type=item.get('punch_type', 'auto'),
            source='offline_sync',
            client_punch_id=item.get('client_punch_id', ''),
            raw_payload=item,
        )
        results.append({
            'client_punch_id': punch.client_punch_id,
            'applied': punch.applied,
            'punch_id': punch.id,
            'error': punch.error_message,
        })
    return results
