"""Training domain HTTP adapters."""
from api.mixins import AuditedModelViewSet, EmployeeQuerysetMixin
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


class SkillViewSet(AuditedModelViewSet):
    queryset = Skill.objects.all().order_by('category', 'name')
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


class EmployeeSkillViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = EmployeeSkillSerializer

    def get_queryset(self):
        qs = EmployeeSkill.objects.select_related('employee', 'skill')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class TrainingCourseViewSet(AuditedModelViewSet):
    queryset = TrainingCourse.objects.all().order_by('-start_date')
    serializer_class = TrainingCourseSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TrainingRecordViewSet(EmployeeQuerysetMixin, AuditedModelViewSet):
    serializer_class = TrainingRecordSerializer

    def get_queryset(self):
        qs = TrainingRecord.objects.select_related('employee', 'course').order_by('-enrolled_date')
        qs = self.scope_to_accessible_employees(qs)
        return qs


class CertificationViewSet(AuditedModelViewSet):
    queryset = Certification.objects.all().order_by('name')
    serializer_class = CertificationSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]


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
