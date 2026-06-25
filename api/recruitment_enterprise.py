from rest_framework import serializers

from recruitment.models import (
    Application,
    ApplicationScorecard,
    HireOnboarding,
    HiringTeamMember,
    JobOffer,
    JobPipelineStage,
    OfferTemplate,
    ScorecardCriterion,
    ScorecardRating,
)
from recruitment.services import render_offer_body


class JobPipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPipelineStage
        fields = ['id', 'job', 'key', 'label', 'order', 'stage_type']


class HiringTeamMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = HiringTeamMember
        fields = ['id', 'job', 'user', 'user_name', 'user_email', 'role']


class ScorecardCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScorecardCriterion
        fields = ['id', 'job', 'name', 'description', 'order', 'weight']


class ScorecardRatingSerializer(serializers.ModelSerializer):
    criterion_name = serializers.CharField(source='criterion.name', read_only=True)

    class Meta:
        model = ScorecardRating
        fields = ['id', 'criterion', 'criterion_name', 'score', 'comment']

    def validate_score(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Score must be between 1 and 5.')
        return value


class ApplicationScorecardSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    recommendation_display = serializers.CharField(source='get_overall_recommendation_display', read_only=True)
    ratings = ScorecardRatingSerializer(many=True, read_only=True)

    class Meta:
        model = ApplicationScorecard
        fields = [
            'id', 'application', 'reviewer', 'reviewer_name',
            'overall_recommendation', 'recommendation_display',
            'summary', 'ratings', 'created_at', 'updated_at',
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']


class ApplicationScorecardWriteSerializer(serializers.ModelSerializer):
    ratings = ScorecardRatingSerializer(many=True)

    class Meta:
        model = ApplicationScorecard
        fields = ['application', 'overall_recommendation', 'summary', 'ratings']

    def create(self, validated_data):
        ratings_data = validated_data.pop('ratings')
        scorecard = ApplicationScorecard.objects.create(
            reviewer=self.context['request'].user,
            **validated_data,
        )
        for rating in ratings_data:
            ScorecardRating.objects.create(scorecard=scorecard, **rating)
        return scorecard

    def update(self, instance, validated_data):
        ratings_data = validated_data.pop('ratings', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if ratings_data is not None:
            instance.ratings.all().delete()
            for rating in ratings_data:
                ScorecardRating.objects.create(scorecard=instance, **rating)
        return instance


class OfferTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferTemplate
        fields = ['id', 'name', 'body', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class JobOfferSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    candidate_name = serializers.SerializerMethodField()
    application_email = serializers.EmailField(source='application.email', read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            'id', 'application', 'template', 'job_title', 'department',
            'salary', 'currency', 'start_date', 'body', 'status', 'status_display',
            'sent_at', 'signed_at', 'signer_name', 'candidate_name', 'application_email',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'sent_at', 'signed_at', 'signer_name', 'signer_ip',
            'created_by', 'created_at', 'updated_at',
        ]

    def get_candidate_name(self, obj):
        return f'{obj.application.first_name} {obj.application.last_name}'


class JobOfferCreateSerializer(serializers.Serializer):
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())
    template = serializers.PrimaryKeyRelatedField(queryset=OfferTemplate.objects.filter(is_active=True))
    salary = serializers.DecimalField(max_digits=14, decimal_places=2)
    start_date = serializers.DateField()
    currency = serializers.CharField(max_length=3, default='KES', required=False)
    job_title = serializers.CharField(max_length=100, required=False)
    department = serializers.CharField(max_length=100, required=False)


class OfferSignSerializer(serializers.Serializer):
    signer_name = serializers.CharField(max_length=100)
    accept = serializers.BooleanField()


class HireOnboardingSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(source='employee_id', read_only=True)

    class Meta:
        model = HireOnboarding
        fields = [
            'id', 'application', 'employee', 'employee_id', 'status',
            'job_title', 'department_name', 'start_date', 'salary',
            'notes', 'candidate_name', 'completed_at', 'created_at',
        ]
        read_only_fields = ['completed_at', 'created_at', 'employee']

    def get_candidate_name(self, obj):
        return f'{obj.application.first_name} {obj.application.last_name}'


class CompleteOnboardingSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=['Male', 'Female', 'Other'])
    address = serializers.CharField(max_length=100)
    emergency_contact = serializers.CharField(max_length=11)
    department = serializers.IntegerField()
    account_number = serializers.CharField(max_length=10)
    bank = serializers.CharField(max_length=25)
    salary = serializers.DecimalField(max_digits=16, decimal_places=2, required=False)
    date_joined = serializers.DateField(required=False)
    job_title = serializers.CharField(max_length=20, required=False)
