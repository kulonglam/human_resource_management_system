from django.test import TestCase

from events.models import DomainEvent
from events.services import drain_outbox, publish_event


class OutboxTests(TestCase):
    def test_publish_and_drain(self):
        event = publish_event('employee.created', {'id': 1})
        self.assertEqual(event.status, DomainEvent.STATUS_PENDING)
        result = drain_outbox(limit=10)
        self.assertEqual(result['processed'], 1)
        event.refresh_from_db()
        self.assertEqual(event.status, DomainEvent.STATUS_PROCESSED)

    def test_handler_failure_marks_failed(self):
        publish_event('leave.approved', {'id': 2})

        def boom(_event):
            raise RuntimeError('nope')

        result = drain_outbox(handler=boom)
        self.assertEqual(result['failed'], 1)
        self.assertEqual(DomainEvent.objects.filter(status=DomainEvent.STATUS_FAILED).count(), 1)
