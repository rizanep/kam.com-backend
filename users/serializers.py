# # users/serializers.py
# from rest_framework import serializers
# from django.contrib.auth import authenticate
# from .models import User
#
#
# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=8)
#
#     class Meta:
#         model = User
#         fields = ('email', 'username', 'password', 'user_type', 'first_name', 'last_name')
#
#     def create(self, validated_data):
#         user = User.objects.create_user(
#             email=validated_data['email'],
#             username=validated_data['username'],
#             password=validated_data['password'],
#             user_type=validated_data['user_type'],
#             first_name=validated_data.get('first_name', ''),
#             last_name=validated_data.get('last_name', '')
#         )
#         return user
#
#
# class UserLoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField()
#
#     def validate(self, data):
#         email = data.get('email')
#         password = data.get('password')
#
#         if email and password:
#             user = authenticate(username=email, password=password)
#             if user:
#                 if user.is_active:
#                     data['user'] = user
#                     return data
#                 raise serializers.ValidationError('User account is disabled.')
#             raise serializers.ValidationError('Unable to login with provided credentials.')
#         raise serializers.ValidationError('Must include "email" and "password".')


# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, UserEducation, UserExperience,
    UserCertification, UserPortfolio, UserSocialLink
)


class UserEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEducation
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UserExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExperience
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UserCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCertification
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UserPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPortfolio
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UserSocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSocialLink
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Comprehensive user profile serializer"""
    profile_picture = serializers.ImageField(use_url=True)

    full_name = serializers.ReadOnlyField()
    education = UserEducationSerializer(many=True, read_only=True)
    experience = UserExperienceSerializer(many=True, read_only=True)
    certifications = UserCertificationSerializer(many=True, read_only=True)
    portfolio = UserPortfolioSerializer(many=True, read_only=True)
    social_links = UserSocialLinkSerializer(many=True, read_only=True)
    groups = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'phone_number', 'profile_picture', 'bio', 'country',
            'city', 'timezone', 'title', 'company_name', 'website',
            'linkedin_url', 'github_url', 'portfolio_url', 'skills',
            'experience_level', 'years_of_experience', 'languages_spoken',
            'hourly_rate', 'currency', 'availability_status',
            'availability_hours_per_week', 'average_rating', 'total_reviews',
            'total_projects_completed', 'company_size', 'industry',
            'total_projects_posted', 'total_spent', 'is_verified',
            'phone_verified', 'identity_verified', 'profile_completion_percentage',
            'last_activity', 'is_featured', 'is_premium', 'premium_expires',
            'notification_preferences', 'privacy_settings', 'created_at',
            'updated_at', 'education', 'experience', 'certifications',
            'portfolio', 'social_links', 'groups'
        ]
        read_only_fields = [
            'id', 'average_rating', 'total_reviews', 'total_projects_completed',
            'total_projects_posted', 'total_spent', 'profile_completion_percentage',
            'last_activity', 'created_at', 'updated_at', 'groups'
        ]

    def validate_hourly_rate(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Hourly rate cannot be negative")
        return value

    def validate_phone_number(self, value):
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Invalid phone number format")
        return value

    def update(self, instance, validated_data):
        # Update the instance
        instance = super().update(instance, validated_data)
        # Recalculate profile completion
        instance.calculate_profile_completion()
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'user_type',
            'phone_number', 'country', 'city', 'password'
        ]



    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)

                # Check if account is locked
                if not user.can_login():
                    if user.is_account_locked:
                        raise serializers.ValidationError(
                            "Account is temporarily locked due to too many failed login attempts"
                        )
                    elif not user.is_active:
                        raise serializers.ValidationError("Account is disabled")

                # Authenticate user
                user = authenticate(request=self.context.get('request'),
                                    username=email, password=password)

                if user:
                    # Reset failed login attempts on successful login
                    user.reset_login_attempts()
                    data['user'] = user
                else:
                    # Increment failed login attempts
                    user_obj = User.objects.get(email=email)
                    user_obj.increment_login_attempts()
                    raise serializers.ValidationError("Invalid credentials")

            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials")
        else:
            raise serializers.ValidationError("Email and password are required")

        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 'profile_picture', 'bio',
            'country', 'city', 'timezone', 'title', 'company_name', 'website',
            'linkedin_url', 'github_url', 'portfolio_url', 'skills',
            'experience_level', 'years_of_experience', 'languages_spoken',
            'hourly_rate', 'currency', 'availability_status',
            'availability_hours_per_week', 'company_size', 'industry',
            'notification_preferences', 'privacy_settings'
        ]
        extra_kwargs = {
            "profile_picture": {"required": False, "allow_null": True},
            "username": {"required": False},
            "email": {"required": False},
        }

    def validate_hourly_rate(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Hourly rate cannot be negative")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.calculate_profile_completion()
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists"""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'user_type',
            'profile_picture', 'title', 'country', 'city', 'average_rating',
            'total_reviews', 'hourly_rate', 'currency', 'availability_status',
            'skills', 'is_verified', 'last_activity'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value