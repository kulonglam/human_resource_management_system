from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import CustomUser, Role
from employees.models import Employee
from departments.models import Department


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True, default=None)
    is_admin = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_name', 'is_admin', 'is_manager',
        ]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate(self, attrs):
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'location', 'history',
            'manager_name', 'manager_contact', 'created_at', 'employee_count',
        ]

    def get_employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'photo', 'photo_url', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'gender', 'email', 'mobile', 'address',
            'emergency_contact', 'language', 'job_title', 'department',
            'department_name', 'date_joined', 'is_active', 'account_number',
            'bank', 'salary', 'termination_date', 'exit_reason', 'exit_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'termination_date', 'exit_reason', 'exit_notes']

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class EmployeeTerminateSerializer(serializers.Serializer):
    exit_reason = serializers.ChoiceField(choices=Employee.EXIT_REASON_CHOICES)
    exit_notes = serializers.CharField(required=False, allow_blank=True)
