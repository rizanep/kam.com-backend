# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.conf.urls.static import static

# Create router for ViewSets
router = DefaultRouter()
router.register(r'profile/education', views.UserEducationViewSet, basename='education')
router.register(r'profile/experience', views.UserExperienceViewSet, basename='experience')
router.register(r'profile/certifications', views.UserCertificationViewSet, basename='certifications')
router.register(r'profile/portfolio', views.UserPortfolioViewSet, basename='portfolio')
router.register(r'profile/social-links', views.UserSocialLinkViewSet, basename='social-links')

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('google/', views.GoogleLoginView.as_view(), name='google_login'),
    path('google-legacy/', views.google_login, name='google_login_legacy'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path("user/", views.GetUserView.as_view(), name="user"),

    # Profile Management
    path('users/profile/', views.CurrentUserProfileView.as_view(), name='current_user_profile'),
    path('profile/update/', views.UpdateUserProfileView.as_view(), name='update_user_profile'),
    path('profile/<int:user_id>/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/completion/update/', views.UpdateProfileCompletionView.as_view(), name='update_profile_completion'),

    # User Search and Listing
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/portfolio/', views.UserPublicPortfolioView.as_view(), name='user_public_portfolio'),

    # Include ViewSet URLs
    path('', include(router.urls)),

    # Admin Views
    path('admin/users/', views.AdminUsersView.as_view(), name='admin_all_users'),
    path('admin/users/assign-group/', views.AssignUserGroupView.as_view(), name='admin_assign_group'),
    path('admin/users/<int:user_id>/toggle-status/', views.ToggleUserStatusView.as_view(), name='admin_toggle_user_status'),
    path('admin/stats/', views.UserStatsView.as_view(), name='admin_user_stats'),

    path('verify-email/send/', views.SendEmailVerificationView.as_view(), name='send_email_verification'),
    path('verify-email/', views.VerifyEmailCodeView.as_view(), name='verify_email_code')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)