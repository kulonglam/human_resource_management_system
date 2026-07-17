"""Disaster recovery targets, drill evidence, and status snapshots."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

DR_STATE_FILE = 'dr_state.json'
DRILL_EVIDENCE_TITLE = 'Monthly restore drill evidence'


def get_dr_targets():
    return {
        'rto_minutes': int(getattr(settings, 'DR_RTO_TARGET_MINUTES', 60)),
        'rpo_hours': int(getattr(settings, 'DR_RPO_TARGET_HOURS', 168)),
        'verify_stale_days': int(getattr(settings, 'DR_VERIFY_STALE_DAYS', 35)),
        'drill_stale_days': int(getattr(settings, 'DR_DRILL_STALE_DAYS', 35)),
    }


def _state_path() -> Path:
    root = Path(settings.BASE_DIR) / 'backups'
    root.mkdir(exist_ok=True)
    return root / DR_STATE_FILE


def _load_state() -> dict:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        logger.exception('Failed to read DR state file')
        return {}


def _save_state(state: dict) -> None:
    path = _state_path()
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding='utf-8')


def record_dr_event(event_type: str, payload: dict) -> dict:
    """Persist verify/drill outcomes for ops dashboards and compliance evidence."""
    now = timezone.now()
    entry = {
        'event_type': event_type,
        'checked_at': now.isoformat(),
        **payload,
    }
    state = _load_state()
    state[event_type] = entry
    _save_state(state)
    cache.set(f'dr:{event_type}', entry, 60 * 60 * 24 * 45)
    return entry


def get_dr_snapshot():
    targets = get_dr_targets()
    state = _load_state()
    latest_backup = _latest_backup_metadata()
    verify = state.get('verify') or cache.get('dr:verify')
    drill = state.get('drill') or cache.get('dr:drill')

    verify_age_days = _age_days(verify)
    drill_age_days = _age_days(drill)
    backup_age_hours = _backup_age_hours(latest_backup)

    within_rpo = backup_age_hours is None or backup_age_hours <= targets['rpo_hours']
    verify_current = verify and verify.get('ok') and (
        verify_age_days is None or verify_age_days <= targets['verify_stale_days']
    )
    drill_current = drill and drill.get('ok') and (
        drill_age_days is None or drill_age_days <= targets['drill_stale_days']
    )
    drill_rto_ok = True
    if drill and drill.get('restore_seconds') is not None:
        drill_rto_ok = drill['restore_seconds'] <= targets['rto_minutes'] * 60

    return {
        'targets': targets,
        'latest_backup': latest_backup,
        'last_verify': verify,
        'last_drill': drill,
        'within_rpo': within_rpo,
        'verify_current': bool(verify_current),
        'drill_current': bool(drill_current),
        'drill_within_rto': drill_rto_ok,
        'ready_for_failover': bool(within_rpo and verify_current and drill_current and drill_rto_ok),
        'documentation': 'DISASTER_RECOVERY.md',
    }


def update_drill_evidence_pack(drill_result: dict) -> None:
    from compliance.models import ComplianceEvidencePack

    today = timezone.now().date()
    description = (
        f"Last drill: {drill_result.get('checked_at', '')}. "
        f"Mode={drill_result.get('mode', 'unknown')}. "
        f"Restore time={drill_result.get('restore_seconds', 'n/a')}s. "
        f"Backup={drill_result.get('backup_name', 'n/a')}."
    )
    pack, _ = ComplianceEvidencePack.objects.update_or_create(
        control='backup_restore',
        title=DRILL_EVIDENCE_TITLE,
        defaults={
            'description': description,
            'owner': 'Ops',
            'status': 'ready' if drill_result.get('ok') else 'gap',
            'last_reviewed_at': today,
            'next_review_at': today + timedelta(days=30),
        },
    )
    return pack


def _latest_backup_metadata():
    from api.backup_storage import list_backup_files

    files = list_backup_files()
    if not files:
        return None
    latest = files[0]
    modified = timezone.datetime.fromtimestamp(
        latest.stat().st_mtime,
        tz=timezone.get_current_timezone(),
    )
    return {
        'name': latest.name,
        'size_bytes': latest.stat().st_size,
        'modified_at': modified.isoformat(),
        'age_hours': round((timezone.now() - modified).total_seconds() / 3600, 2),
    }


def _age_days(entry):
    if not entry or not entry.get('checked_at'):
        return None
    checked = timezone.datetime.fromisoformat(entry['checked_at'])
    if timezone.is_naive(checked):
        checked = timezone.make_aware(checked, timezone.get_current_timezone())
    return (timezone.now() - checked).total_seconds() / 86400


def _backup_age_hours(latest_backup):
    if not latest_backup:
        return None
    return latest_backup.get('age_hours')


def collect_dr_alerts():
    snapshot = get_dr_snapshot()
    targets = snapshot['targets']
    alerts = []

    if snapshot['latest_backup'] is None:
        alerts.append({
            'key': 'dr_no_backup',
            'level': 'error',
            'title': 'HRMIS DR: no backups found',
            'message': 'No local backup artifacts exist under backups/. Run backup_database.',
            'details': snapshot,
        })
    elif not snapshot['within_rpo']:
        alerts.append({
            'key': 'dr_rpo_breach',
            'level': 'error',
            'title': 'HRMIS DR: RPO target breached',
            'message': (
                f"Latest backup is {snapshot['latest_backup']['age_hours']}h old; "
                f"target RPO is {targets['rpo_hours']}h."
            ),
            'details': snapshot,
        })

    if not snapshot['verify_current']:
        alerts.append({
            'key': 'dr_verify_stale',
            'level': 'warning',
            'title': 'HRMIS DR: backup verification stale or failed',
            'message': (
                'Run verify_backup on staging or production and record the result. '
                f"Stale threshold is {targets['verify_stale_days']} days."
            ),
            'details': snapshot,
        })

    if not snapshot['drill_current']:
        alerts.append({
            'key': 'dr_drill_stale',
            'level': 'warning',
            'title': 'HRMIS DR: restore drill stale or failed',
            'message': (
                'Run run_restore_drill on staging monthly. '
                f"Stale threshold is {targets['drill_stale_days']} days."
            ),
            'details': snapshot,
        })
    elif not snapshot['drill_within_rto']:
        alerts.append({
            'key': 'dr_rto_breach',
            'level': 'warning',
            'title': 'HRMIS DR: restore drill exceeded RTO',
            'message': (
                f"Last drill restore time exceeded target RTO of {targets['rto_minutes']} minutes."
            ),
            'details': snapshot,
        })

    return alerts
