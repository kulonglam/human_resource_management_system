from django.core.management.base import BaseCommand

from accounts.models import Role
from documents.models import DocumentAccessRule, HRDocument


DEFAULT_RULES = {
    Role.ADMIN: {category: {'can_view': True, 'can_upload': True} for category, _ in HRDocument.CATEGORY_CHOICES},
    Role.MANAGER: {
        'contract': {'can_view': False, 'can_upload': False},
        'policy': {'can_view': True, 'can_upload': True},
        'offer_letter': {'can_view': True, 'can_upload': False},
        'certificate': {'can_view': True, 'can_upload': True},
        'other': {'can_view': True, 'can_upload': True},
    },
    Role.EMPLOYEE: {
        'contract': {'can_view': False, 'can_upload': False},
        'policy': {'can_view': True, 'can_upload': False},
        'offer_letter': {'can_view': False, 'can_upload': False},
        'certificate': {'can_view': True, 'can_upload': False},
        'other': {'can_view': True, 'can_upload': False},
    },
}


class Command(BaseCommand):
    help = 'Seed default document access rules by role and category.'

    def handle(self, *args, **options):
        created = 0
        for role_name, categories in DEFAULT_RULES.items():
            role = Role.objects.filter(name=role_name).first()
            if not role:
                continue
            for category, perms in categories.items():
                _, was_created = DocumentAccessRule.objects.update_or_create(
                    role=role,
                    category=category,
                    defaults=perms,
                )
                if was_created:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Document access rules ready ({created} created).'))
