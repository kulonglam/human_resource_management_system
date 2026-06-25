from django.core.management.base import BaseCommand

from workflows.models import ApprovalStep, ApprovalWorkflow


DEFAULT_WORKFLOWS = [
    {
        'name': 'Standard Leave Approval',
        'workflow_type': 'leave',
        'extra_step_min_days': 5,
        'steps': [
            {'step_order': 1, 'label': 'Manager Review', 'approver_type': 'manager'},
            {'step_order': 2, 'label': 'HR Review', 'approver_type': 'admin'},
        ],
    },
    {
        'name': 'Standard Expense Approval',
        'workflow_type': 'expense',
        'extra_step_min_amount': 10000,
        'steps': [
            {'step_order': 1, 'label': 'Manager Review', 'approver_type': 'manager'},
            {'step_order': 2, 'label': 'HR Review', 'approver_type': 'admin'},
        ],
    },
    {
        'name': 'Recruitment Hiring Approval',
        'workflow_type': 'recruitment',
        'steps': [
            {'step_order': 1, 'label': 'Hiring Manager Review', 'approver_type': 'manager'},
            {'step_order': 2, 'label': 'HR Final Approval', 'approver_type': 'admin'},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed default multi-step approval workflows.'

    def handle(self, *args, **options):
        for spec in DEFAULT_WORKFLOWS:
            workflow, created = ApprovalWorkflow.objects.update_or_create(
                workflow_type=spec['workflow_type'],
                is_default=True,
                defaults={
                    'name': spec['name'],
                    'is_active': True,
                    'extra_step_min_days': spec.get('extra_step_min_days'),
                    'extra_step_min_amount': spec.get('extra_step_min_amount'),
                },
            )
            workflow.steps.all().delete()
            for step in spec['steps']:
                ApprovalStep.objects.create(workflow=workflow, **step)
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} workflow: {workflow.name}')
