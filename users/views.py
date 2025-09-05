# # users/views.py - Updated with group functionality
# from rest_framework import status
# from rest_framework.views import APIView
# from .serializers import UserRegistrationSerializer, UserLoginSerializer
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.response import Response
# from google.auth.transport import requests
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from django.contrib.auth import get_user_model
# from rest_framework_simplejwt.tokens import RefreshToken
# from google.oauth2 import id_token
# from google.auth.transport import requests as google_requests
# import json
# import requests
# from django.core.files.base import ContentFile
# import string
# import random
# from django.contrib.auth.models import Group
# from django.core.exceptions import PermissionDenied
# from functools import wraps
#
# User = get_user_model()
#
#
# # Helper functions
# def save_profile_picture_from_url(user, url):
#     if not url:
#         return
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             user.profile_picture.save(
#                 f"{user.pk}.jpg",  # filename
#                 ContentFile(response.content),
#                 save=True
#             )
#     except Exception:
#         pass
#
#
# def generate_random_password(length=12):
#     """Generate a secure random password"""
#     chars = string.ascii_letters + string.digits + string.punctuation
#     return ''.join(random.choice(chars) for _ in range(length))
#
#
# def assign_user_to_group(user, group_name):
#     """Assign user to a specific group"""
#     try:
#         group = Group.objects.get(name=group_name)
#         user.groups.add(group)
#         return True
#     except Group.DoesNotExist:
#         return False
#
#
# # Permission decorator
# def has_group_permission(group_names):
#     """
#     Decorator to check if user belongs to specific groups
#     Usage: @has_group_permission(['Admin', 'Moderator'])
#     """
#     if isinstance(group_names, str):
#         group_names = [group_names]
#
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             if request.user.is_authenticated:
#                 user_groups = request.user.groups.values_list('name', flat=True)
#                 if any(group in user_groups for group in group_names):
#                     return view_func(request, *args, **kwargs)
#             raise PermissionDenied("You don't have permission to access this resource")
#
#         return _wrapped_view
#
#     return decorator
#
#
# @csrf_exempt
# def google_login(request):
#     if request.method == "POST":
#         try:
#             body = json.loads(request.body)
#             token = body.get("credential")
#
#             if not token:
#                 return JsonResponse({"error": "credential missing"}, status=400)
#
#             # Verify token with Google
#             idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
#
#             email = idinfo.get("email")
#             name = idinfo.get("name")
#             picture_url = idinfo.get("picture")  # Google profile picture URL
#
#             if not email:
#                 return JsonResponse({"error": "Invalid token: no email"}, status=400)
#
#             # Get or create user
#             user, created = User.objects.get_or_create(
#                 email=email,
#                 defaults={
#                     "username": email.split("@")[0],
#                     "first_name": name.split(" ")[0] if name else "",
#                     "last_name": " ".join(name.split(" ")[1:]) if name and len(name.split(" ")) > 1 else "",
#                     "user_type": "client",  # default user type
#                 }
#             )
#
#             # ✅ Set a password for new users and assign to group
#             if created:
#                 random_password = generate_random_password()
#                 user.set_password(random_password)
#                 user.save()
#                 # Assign to Client group by default
#                 assign_user_to_group(user, 'Client')
#
#             # Save Google profile picture if missing
#             if picture_url and (created or not user.profile_picture):
#                 save_profile_picture_from_url(user, picture_url)
#
#             # Generate JWT tokens
#             refresh = RefreshToken.for_user(user)
#
#             # Get user groups and permissions
#             user_groups = list(user.groups.values_list('name', flat=True))
#             user_permissions = list(user.get_all_permissions())
#
#             return JsonResponse({
#                 "user": {
#                     "id": user.id,
#                     "email": user.email,
#                     "username": user.username,
#                     "name": f"{user.first_name} {user.last_name}".strip(),
#                     "profile_picture": user.profile_picture.url if user.profile_picture else None,
#                     "groups": user_groups,
#                     "permissions": user_permissions,
#                 },
#                 "refresh": str(refresh),
#                 "access": str(refresh.access_token),
#                 "created": created
#             })
#
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)
#
#     return JsonResponse({"error": "Invalid request"}, status=405)
#
#
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_user(request):
#     user = request.user
#     user_groups = list(user.groups.values_list('name', flat=True))
#     user_permissions = list(user.get_all_permissions())
#
#     return Response({
#         "id": user.id,
#         "username": user.username,
#         "email": user.email,
#         "groups": user_groups,
#         "permissions": user_permissions,
#     })
#
#
# # New admin-only endpoint
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_all_users(request):
#     """Only Admin can view all users"""
#     # Check if user is in Admin group
#     if not request.user.groups.filter(name='Admin').exists():
#         return Response({"error": "You don't have permission to access this resource"},
#                         status=status.HTTP_403_FORBIDDEN)
#
#     users = User.objects.all()
#     users_data = []
#     for user in users:
#         users_data.append({
#             "id": user.id,
#             "username": user.username,
#             "email": user.email,
#             "groups": list(user.groups.values_list('name', flat=True)),
#             "is_active": user.is_active,
#         })
#     return Response({"users": users_data})
#
#
# # New admin-only endpoint to assign users to groups
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def assign_user_group(request):
#     """Admin can assign users to groups"""
#     # Check if user is in Admin group
#     if not request.user.groups.filter(name='Admin').exists():
#         return Response({"error": "You don't have permission to access this resource"},
#                         status=status.HTTP_403_FORBIDDEN)
#
#     user_id = request.data.get('user_id')
#     group_name = request.data.get('group_name')
#
#     if not user_id or not group_name:
#         return Response({"error": "user_id and group_name are required"}, status=400)
#
#     try:
#         user = User.objects.get(id=user_id)
#         group = Group.objects.get(name=group_name)
#
#         # Remove user from all groups first (optional)
#         user.groups.clear()
#         # Assign to new group
#         user.groups.add(group)
#
#         return Response({
#             "message": f"User {user.username} assigned to {group_name} group",
#             "user_groups": list(user.groups.values_list('name', flat=True))
#         })
#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=400)
#     except Group.DoesNotExist:
#         return Response({"error": "Group not found"}, status=400)
#
#
# class RegisterView(APIView):
#     def post(self, request):
#         serializer = UserRegistrationSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#
#             # Assign to Client group by default
#             assign_user_to_group(user, 'Client')
#
#             refresh = RefreshToken.for_user(user)
#             user_groups = list(user.groups.values_list('name', flat=True))
#             user_permissions = list(user.get_all_permissions())
#
#             return Response({
#                 'user': {
#                     **serializer.data,
#                     'groups': user_groups,
#                     'permissions': user_permissions,
#                 },
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             }, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# class LoginView(APIView):
#     def post(self, request):
#         serializer = UserLoginSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.validated_data['user']
#             refresh = RefreshToken.for_user(user)
#             user_groups = list(user.groups.values_list('name', flat=True))
#             user_permissions = list(user.get_all_permissions())
#
#             return Response({
#                 'user': {
#                     'id': user.id,
#                     'email': user.email,
#                     'user_type': user.user_type,
#                     'groups': user_groups,
#                     'permissions': user_permissions,
#                 },
#                 'refresh': str(refresh),
#                 'access': str(refresh.access_token),
#             })
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# users/views.py - Enhanced with full profile functionality
from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import json
import requests
from django.core.files.base import ContentFile
import string
import random
from functools import wraps

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


# Permission decorator
def has_group_permission(group_names):
    """
    Decorator to check if user belongs to specific groups
    Usage: @has_group_permission(['Admin', 'Moderator'])
    """
    if isinstance(group_names, str):
        group_names = [group_names]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                user_groups = request.user.groups.values_list('name', flat=True)
                if any(group in user_groups for group in group_names):
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied("You don't have permission to access this resource")

        return _wrapped_view

    return decorator

@csrf_exempt
def google_login(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            token = body.get("credential")
            requested_user_type = body.get("user_type")  # Get from frontend

            if not token:
                return JsonResponse({"error": "credential missing"}, status=400)

            # Verify token with Google
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request())

            email = idinfo.get("email")
            name = idinfo.get("name")
            picture_url = idinfo.get("picture")

            if not email:
                return JsonResponse({"error": "Invalid token: no email"}, status=400)

            user = User.objects.filter(email=email).first()

            if not user:
                # Validate user_type from request
                if not requested_user_type:
                    return JsonResponse({"error": "user_type is required for registration"}, status=400)

                if requested_user_type not in ["client", "freelancer"]:
                    return JsonResponse({"error": "Invalid user_type"}, status=400)

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

            return JsonResponse({
                "user": serializer.data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "created": created
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
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


# Profile Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user_profile(request):
    """Get current user's complete profile"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """Update current user's profile"""
    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        profile_serializer = UserProfileSerializer(request.user)
        return Response(profile_serializer.data)
    else:
        print(serializer.errors)  # 👈 add this
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def change_password(request):
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


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_profile(request, user_id):
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


# Education Management Views
class UserEducationListCreateView(generics.ListCreateAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserEducationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserEducationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)


# Experience Management Views
class UserExperienceListCreateView(generics.ListCreateAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is marked as current, unmark other current jobs
        if serializer.validated_data.get('is_current'):
            UserExperience.objects.filter(user=self.request.user, is_current=True).update(is_current=False)
        serializer.save(user=self.request.user)


class UserExperienceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # If this is marked as current, unmark other current jobs
        if serializer.validated_data.get('is_current'):
            UserExperience.objects.filter(user=self.request.user, is_current=True).exclude(
                id=self.get_object().id).update(is_current=False)
        serializer.save()


# Certification Management Views
class UserCertificationListCreateView(generics.ListCreateAPIView):
    serializer_class = UserCertificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserCertificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserCertificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserCertification.objects.filter(user=self.request.user)


# Portfolio Management Views
class UserPortfolioListCreateView(generics.ListCreateAPIView):
    serializer_class = UserPortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPortfolio.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserPortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserPortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserPortfolio.objects.filter(user=self.request.user)


# Social Links Management Views
class UserSocialLinkListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSocialLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSocialLink.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserSocialLinkDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSocialLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSocialLink.objects.filter(user=self.request.user)


# Admin Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """Admin only - Get all users with pagination and filtering"""
    if not request.user.groups.filter(name='Admin').exists():
        return Response({"error": "You don't have permission to access this resource"},
                        status=status.HTTP_403_FORBIDDEN)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_user_group(request):
    """Admin can assign users to groups"""
    if not request.user.groups.filter(name='Admin').exists():
        return Response({"error": "You don't have permission to access this resource"},
                        status=status.HTTP_403_FORBIDDEN)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_status(request, user_id):
    """Admin can activate/deactivate users"""
    if not request.user.groups.filter(name='Admin').exists():
        return Response({"error": "You don't have permission to access this resource"},
                        status=status.HTTP_403_FORBIDDEN)

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
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stats(request):
    """Get platform statistics (Admin only)"""
    if not request.user.groups.filter(name='Admin').exists():
        return Response({"error": "You don't have permission to access this resource"},
                        status=status.HTTP_403_FORBIDDEN)

    total_users = User.objects.count()
    total_freelancers = User.objects.filter(user_type='freelancer').count()
    total_clients = User.objects.filter(user_type='client').count()
    verified_users = User.objects.filter(is_verified=True).count()
    premium_users = User.objects.filter(is_premium=True).count()

    # Get users by country (top 10)
    from django.db.models import Count
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile_completion(request):
    """Manually trigger profile completion calculation"""
    user = request.user
    percentage = user.calculate_profile_completion()
    user.save()

    return Response({
        "message": "Profile completion updated",
        "profile_completion_percentage": percentage
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_public_portfolio(request, user_id):
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