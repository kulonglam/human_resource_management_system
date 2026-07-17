"""Training domain serializers."""
from rest_framework import serializers

from training.models import (
    Certification,
    DevelopmentPlan,
    EmployeeCertification,
    EmployeeSkill,
    Skill,
    TrainingCourse,
    TrainingRecord,
)

class SkillSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = '__all__'



class EmployeeSkillSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = '__all__'



class TrainingCourseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    participants_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingCourse
        fields = '__all__'



class TrainingRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TrainingRecord
        fields = '__all__'



class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'



class EmployeeCertificationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    certification_name = serializers.CharField(source='certification.name', read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmployeeCertification
        fields = '__all__'



class DevelopmentPlanSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DevelopmentPlan
        fields = '__all__'



