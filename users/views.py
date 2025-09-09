from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status, generics, filters, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
from django.core.files.base import ContentFile
import string
import random

from .models import (
    User, UserEducation, UserExperience,
    UserCertification, UserPortfolio, UserSocialLink
)
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserUpdateSerializer, UserListSerializer, ChangePasswordSerializer,
    UserEducationSerializer, UserExperienceSerializer,
    UserCertificationSerializer, UserPortfolioSerializer, UserSocialLinkSerializer
)

User = get_user_model()


# Pagination class
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Helper functions
def save_profile_picture_from_url(user, url):
    if not url:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            user.profile_picture.save(
                f"{user.pk}.jpg",
                ContentFile(response.content),
                save=True
            )
    except Exception:
        pass


def generate_random_password(length=12):
    """Generate a secure random password"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def assign_user_to_group(user, group_name):
    """Assign user to a specific group"""
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        return True
    except Group.DoesNotExist:
        return False



# Custom Permission Classes
class IsAdminUser(IsAuthenticated):

    def has_permission(self, request, view):
        return (super().has_permission(request, view) and
                request.user.groups.filter(name='Admin').exists())


# Authentication Views
@method_decorator(csrf_exempt, name='dispatch')
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            token = request.data.get("credential")
            requested_user_type = request.data.get("user_type")

            if not token:
                return Response({"error": "credential missing"}, status=400)

            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request())

            email = idinfo.get("email")
            name = idinfo.get("name")
            picture_url = idinfo.get("picture")

            if not email:
                return Response({"error": "Invalid token: no email"}, status=400)

            user = User.objects.filter(email=email).first()

            if not user:
                # Validate user_type from request
                if not requested_user_type:
                    return Response({"error": "user_type is required for registration"}, status=400)

                if requested_user_type not in ["client", "freelancer"]:
                    return Response({"error": "Invalid user_type"}, status=400)

                # Create new user with provided type
                user = User.objects.create(
                    email=email,
                    username=email.split("@")[0],
                    first_name=name.split(" ")[0] if name else "",
                    last_name=" ".join(name.split(" ")[1:]) if name and len(name.split(" ")) > 1 else "",
                    user_type=requested_user_type,
                )

                random_password = generate_random_password()
                user.set_password(random_password)
                user.calculate_profile_completion()
                user.save()

                # Assign group according to user_type
                assign_user_to_group(user, requested_user_type)

                created = True
            else:
                # Existing user - must keep their saved type
                created = False

            # Save Google profile picture if missing
            if picture_url and (created or not user.profile_picture):
                save_profile_picture_from_url(user, picture_url)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            serializer = UserProfileSerializer(user)

            return Response({
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "created": created
            })

        except Exception as e:
            return Response({"error": str(e)}, status=400)


class GetUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_groups = list(user.groups.values_list('name', flat=True))
        user_permissions = list(user.get_all_permissions())

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "groups": user_groups,
            "permissions": user_permissions,
        })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Assign to appropriate group
            group_name = 'Freelancer' if user.user_type == 'freelancer' else 'Client'
            assign_user_to_group(user, group_name)

            refresh = RefreshToken.for_user(user)
            profile_serializer = UserProfileSerializer(user)

            return Response({
                'user': profile_serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            profile_serializer = UserProfileSerializer(user)

            # Update last login IP
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.save(update_fields=['last_login_ip'])

            return Response({
                'user': profile_serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password changed successfully"})
        else:
            print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Profile Views
class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's complete profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UpdateUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Update current user's profile"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            profile_serializer = UserProfileSerializer(request.user)
            return Response(profile_serializer.data)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Partially update current user's profile"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            profile_serializer = UserProfileSerializer(request.user)
            return Response(profile_serializer.data)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        """Get public profile of any user"""
        try:
            user = User.objects.get(id=user_id, is_active=True)
            serializer = UserProfileSerializer(user)

            # Remove sensitive data for public view
            data = serializer.data
            sensitive_fields = [
                'email', 'phone_number', 'last_login_ip', 'notification_preferences',
                'privacy_settings', 'is_verified', 'phone_verified', 'identity_verified'
            ]
            for field in sensitive_fields:
                data.pop(field, None)

            return Response(data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


# User Search and Filtering
class UserListView(generics.ListAPIView):
    """List and search users with filtering"""
    serializer_class = UserListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'country', 'availability_status', 'experience_level']
    search_fields = ['first_name', 'last_name', 'title', 'skills', 'bio']
    ordering_fields = ['average_rating', 'hourly_rate', 'total_reviews', 'created_at']
    ordering = ['-average_rating']

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)

        # Filter by skills if provided
        skills = self.request.query_params.get('skills')
        if skills:
            skill_list = [skill.strip() for skill in skills.split(',')]
            queryset = queryset.filter(skills__overlap=skill_list)

        # Filter by hourly rate range
        min_rate = self.request.query_params.get('min_rate')
        max_rate = self.request.query_params.get('max_rate')
        if min_rate:
            queryset = queryset.filter(hourly_rate__gte=min_rate)
        if max_rate:
            queryset = queryset.filter(hourly_rate__lte=max_rate)

        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        return queryset


# Education Management ViewSet
class UserEducationViewSet(viewsets.ModelViewSet):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



# Experience Management ViewSet
class UserExperienceViewSet(viewsets.ModelViewSet):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is marked as current, unmark other current jobs
        if serializer.validated_data.get('is_current'):
            UserExperience.objects.filter(user=self.request.user, is_current=True).update(is_current=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # If this is marked as current, unmark other current jobs
        if serializer.validated_data.get('is_current'):
            UserExperience.objects.filter(user=self.request.user, is_current=True).exclude(
                id=self.get_object().id).update(is_current=False)
        serializer.save()


# Certification Management ViewSet
class UserCertificationViewSet(viewsets.ModelViewSet):
    serializer_class = UserCertificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Portfolio Management ViewSet
class UserPortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = UserPortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPortfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Social Links Management ViewSet
class UserSocialLinkViewSet(viewsets.ModelViewSet):
    serializer_class = UserSocialLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSocialLink.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Admin Views
class AdminUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Admin only - Get all users with pagination and filtering"""
        # Apply filtering
        queryset = User.objects.all()
        user_type = request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)

        # Apply search
        search = request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )

        # Pagination
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        users_data = []
        for user in result_page:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "groups": list(user.groups.values_list('name', flat=True)),
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "profile_completion_percentage": user.profile_completion_percentage,
                "created_at": user.created_at,
                "last_activity": user.last_activity,
            })

        return paginator.get_paginated_response(users_data)


class AssignUserGroupView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Admin can assign users to groups"""
        user_id = request.data.get('user_id')
        group_name = request.data.get('group_name')

        if not user_id or not group_name:
            return Response({"error": "user_id and group_name are required"}, status=400)

        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name=group_name)

            # Optionally remove from all groups first
            clear_groups = request.data.get('clear_groups', False)
            if clear_groups:
                user.groups.clear()

            user.groups.add(group)

            return Response({
                "message": f"User {user.username} assigned to {group_name} group",
                "user_groups": list(user.groups.values_list('name', flat=True))
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=400)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=400)


class ToggleUserStatusView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        """Admin can activate/deactivate users"""
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()

            return Response({
                "message": f"User {user.username} {'activated' if user.is_active else 'deactivated'}",
                "is_active": user.is_active
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=400)


# Statistics and Analytics Views
class UserStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get platform statistics (Admin only)"""
        total_users = User.objects.count()
        total_freelancers = User.objects.filter(user_type='freelancer').count()
        total_clients = User.objects.filter(user_type='client').count()
        verified_users = User.objects.filter(is_verified=True).count()
        premium_users = User.objects.filter(is_premium=True).count()

        # Get users by country (top 10)
        users_by_country = User.objects.values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            "total_users": total_users,
            "total_freelancers": total_freelancers,
            "total_clients": total_clients,
            "verified_users": verified_users,
            "premium_users": premium_users,
            "verification_rate": (verified_users / total_users * 100) if total_users > 0 else 0,
            "users_by_country": users_by_country,
        })


# Utility Views
class UpdateProfileCompletionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Manually trigger profile completion calculation"""
        user = request.user
        percentage = user.calculate_profile_completion()
        user.save()

        return Response({
            "message": "Profile completion updated",
            "profile_completion_percentage": percentage
        })


class UserPublicPortfolioView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        """Get user's public portfolio items"""
        try:
            user = User.objects.get(id=user_id, is_active=True, user_type='freelancer')
            portfolio_items = UserPortfolio.objects.filter(user=user)
            serializer = UserPortfolioSerializer(portfolio_items, many=True)

            return Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "title": user.title,
                    "profile_picture": user.profile_picture.url if user.profile_picture else None,
                    "bio": user.bio,
                    "skills": user.skills,
                    "average_rating": user.average_rating,
                    "total_reviews": user.total_reviews,
                },
                "portfolio": serializer.data
            })
        except User.DoesNotExist:
            return Response({"error": "Freelancer not found"}, status=404)


# Legacy function for Google login (keeping for backward compatibility)
@csrf_exempt
def google_login(request):
    view = GoogleLoginView.as_view()
    return view(request)

class SendEmailVerificationView(APIView):
    """Send email verification code to user's email address"""
    permission_classes = [IsAuthenticated]  # must be logged in

    def post(self, request):
        try:
            user = request.user

            # Check if email is already verified
            if user.is_verified:
                return Response(
                    {'error': 'Email is already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate new verification code
            verification_code = user.generate_email_verification_token()

            # Send email
            subject = 'Verify Your Email Address'
            message = f"""
Hi {user.full_name or user.username},

Please use the following code to verify your email address:

{verification_code}

This code will expire in 15 minutes.

If you didn't request this verification, please ignore this email.

Best regards,
Your App Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response(
                {'message': 'Verification code sent to your email'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': f'Failed to send verification email: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailCodeView(APIView):
    """Verify email using the provided code"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            code = request.data.get('code', '').strip()

            if not code:
                return Response(
                    {'error': 'Verification code is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if len(code) != 6 or not code.isdigit():
                return Response(
                    {'error': 'Invalid verification code format'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if email is already verified
            if user.is_verified:
                return Response(
                    {'error': 'Email is already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if verification token exists
            if not user.email_verification_token:
                return Response(
                    {'error': 'No verification code found. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate the token
            if not user.is_email_verification_token_valid(code):
                if user.email_verification_expires and timezone.now() > user.email_verification_expires:
                    user.clear_email_verification_token()
                    return Response(
                        {'error': 'Verification code has expired. Please request a new one.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'error': 'Invalid verification code'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Mark email as verified and clear token
            user.is_verified = True
            user.clear_email_verification_token()
            user.save(update_fields=['is_verified'])

            return Response(
                {'message': 'Email verified successfully'},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {'error': f'An unexpected error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
