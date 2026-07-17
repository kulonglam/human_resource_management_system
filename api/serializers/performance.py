"""Performance domain serializers."""
from rest_framework import serializers

from performance.models import Feedback, FeedbackRequest, FeedbackRound, PerformanceAppraisal, PerformanceGoal

class PerformanceGoalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PerformanceGoal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PerformanceAppraisal
        fields = '__all__'
        read_only_fields = ['overall_rating', 'created_at', 'submitted_at', 'reviewed_at', 'approved_at']



class FeedbackRoundSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FeedbackRound
        fields = '__all__'
        read_only_fields = ['created_at']



class FeedbackRequestSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    giver_username = serializers.CharField(source='feedback_giver.username', read_only=True)
    round_name = serializers.CharField(source='feedback_round.name', read_only=True)
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'submitted_at']

    def get_has_feedback(self, obj):
        return hasattr(obj, 'feedback')



class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



