"""Training domain HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin, OrganizationQuerysetMixin
from api.permissions import IsAdminOrManagerOrReadOnly
from api.serializers import (
    CertificationSerializer,
    DevelopmentPlanSerializer,
    EmployeeCertificationSerializer,
    EmployeeSkillSerializer,
    SkillSerializer,
    TrainingCourseSerializer,
    TrainingRecordSerializer,
)
from training.models import (
    Certification,
    DevelopmentPlan,
    EmployeeCertification,
    EmployeeSkill,
    Skill,
    TrainingCourse,
    TrainingRecord,
)


class SkillViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(Skill.objects.all().order_by('category', 'name'))


class EmployeeSkillViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeSkillSerializer

    def get_queryset(self):
        qs = EmployeeSkill.objects.select_related('employee', 'skill')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class TrainingCourseViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(TrainingCourse.objects.all().order_by('-start_date'))

    def perform_create(self, serializer):
        kwargs = {'created_by': self.request.user}
        org_id = getattr(self.request.user, 'organization_id', None)
        if org_id and not serializer.validated_data.get('organization'):
            kwargs['organization_id'] = org_id
        serializer.save(**kwargs)


class TrainingRecordViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = TrainingRecordSerializer

    def get_queryset(self):
        qs = TrainingRecord.objects.select_related('employee', 'course').order_by('-enrolled_date')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class CertificationViewSet(OrganizationQuerysetMixin, AuditedModelViewSet):
    serializer_class = CertificationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def get_queryset(self):
        return self.scope_to_organization(Certification.objects.all().order_by('name'))


class EmployeeCertificationViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeCertificationSerializer

    def get_queryset(self):
        qs = EmployeeCertification.objects.select_related('employee', 'certification')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class DevelopmentPlanViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = DevelopmentPlanSerializer

    def get_queryset(self):
        qs = DevelopmentPlan.objects.select_related('employee').order_by('-created_at')
        qs = self.scope_to_accessible_employees(qs)
        return qs
