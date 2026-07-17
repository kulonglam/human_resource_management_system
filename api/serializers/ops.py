"""Ops domain serializers."""
from rest_framework import serializers

from assets.models import Asset, AssetAssignment
from benefits.models import Benefit, EmployeeBenefit
from discipline.models import Discipline, DisciplineAppeal
from exits.models import ExitChecklist, ExitProcess
from expenses.models import Expense, ExpenseCategory
from kin.models import Kin
from shifts.models import Shift, ShiftAssignment
from surveys.models import Survey, SurveyQuestion, SurveyResponse
from workflows.services import approval_status_payload

class ExitProcessSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = ExitProcess
        fields = '__all__'



class ExitChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExitChecklist
        fields = '__all__'



class AssetSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_current_status_display', read_only=True)

    class Meta:
        model = Asset
        fields = '__all__'



class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AssetAssignment
        fields = '__all__'



class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'



class ShiftAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    shift_name = serializers.CharField(source='shift.shift_name', read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = '__all__'



class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'



class ExpenseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    receipt_url = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = '__all__'

    def get_approval_status(self, obj):
        return approval_status_payload(obj)

    def get_receipt_url(self, obj):
        if obj.receipt_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_file.url)
            return obj.receipt_file.url
        return None



class BenefitSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_benefit_type_display', read_only=True)

    class Meta:
        model = Benefit
        fields = '__all__'



class EmployeeBenefitSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    benefit_name = serializers.CharField(source='benefit.name', read_only=True)

    class Meta:
        model = EmployeeBenefit
        fields = '__all__'



class DisciplineSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    type_display = serializers.CharField(source='get_discipline_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Discipline
        fields = '__all__'



class DisciplineAppealSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DisciplineAppeal
        fields = '__all__'



class KinSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Kin
        fields = '__all__'



class SurveySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Survey
        fields = '__all__'



class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'



class SurveyResponseSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = SurveyResponse
        fields = '__all__'



