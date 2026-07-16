"""Document category access by role."""

from documents.models import DocumentAccessRule, HRDocument


def user_can_view_document_category(user, category):
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    if not user.role:
        return category != 'contract'
    rule = DocumentAccessRule.objects.filter(role=user.role, category=category).first()
    if rule:
        return rule.can_view
    if user.is_manager:
        return category in ('policy', 'offer_letter', 'certificate', 'other')
    return category in ('policy', 'certificate', 'other')


def user_can_upload_document_category(user, category):
    if user.is_admin:
        return True
    if not user.role:
        return False
    rule = DocumentAccessRule.objects.filter(role=user.role, category=category).first()
    if rule:
        return rule.can_upload
    return user.is_manager and category in ('policy', 'certificate', 'other')


def filter_documents_for_user(queryset, user):
    if user.is_admin:
        return queryset
    allowed = [
        category for category, _ in HRDocument.CATEGORY_CHOICES
        if user_can_view_document_category(user, category)
    ]
    return queryset.filter(category__in=allowed)
