"""Compliance evidence helpers for security assurance and load proof."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

LOADTEST_EVIDENCE_TITLE = 'Load / soak test evidence'
PENTEST_EVIDENCE_TITLE = 'Penetration test report'
ACCESS_REVIEW_EVIDENCE_TITLE = 'Privileged access review'


def record_assurance_event(
    *,
    control: str,
    title: str,
    ok: bool,
    description: str = '',
    evidence_url: str = '',
    owner: str = 'Security',
    review_days: int = 90,
):
    """Create or update a ComplianceEvidencePack row for an assurance activity."""
    from compliance.models import ComplianceEvidencePack

    today = timezone.now().date()
    pack, _ = ComplianceEvidencePack.objects.update_or_create(
        control=control,
        title=title,
        defaults={
            'description': description,
            'evidence_url': evidence_url,
            'owner': owner,
            'status': 'ready' if ok else 'gap',
            'last_reviewed_at': today,
            'next_review_at': today + timedelta(days=review_days),
        },
    )
    return pack


def update_loadtest_evidence_pack(
    *,
    ok: bool,
    requests: int = 0,
    error_rate: float = 0.0,
    median_ms: float = 0.0,
    p95_ms: float = 0.0,
    notes: str = '',
    evidence_url: str = '',
):
    description = (
        f'Load test recorded at {timezone.now().isoformat()}. '
        f'requests={requests} error_rate={error_rate:.4f} '
        f'median_ms={median_ms:.0f} p95_ms={p95_ms:.0f}. '
        f'{notes}'.strip()
    )
    return record_assurance_event(
        control='availability_slo',
        title=LOADTEST_EVIDENCE_TITLE,
        ok=ok,
        description=description,
        evidence_url=evidence_url,
        owner='Ops',
        review_days=30,
    )
