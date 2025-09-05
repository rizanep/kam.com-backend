# # users/urls.py
# from django.urls import path, include
# from .views import RegisterView, LoginView, get_user, google_login, assign_user_group
#
# urlpatterns = [
#     path('register/', RegisterView.as_view(), name='register'),
#     path('login/', LoginView.as_view(), name='login'),
#     path("user/", get_user, name="user"),
#     path('accounts/', include('allauth.urls')),
#     path('google/', google_login, name="google_login"),
#     path('asign/', assign_user_group, name="group"),
# ]


# users/urls.py
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('google/', views.google_login, name='google_login'),
    path('change-password/', views.change_password, name='change_password'),
    path("user/", views.get_user, name="user"),

    # Profile Management
    path('users/profile/', views.get_current_user_profile, name='current_user_profile'),
    path('profile/update/', views.update_user_profile, name='update_user_profile'),
    path('profile/<int:user_id>/', views.get_user_profile, name='user_profile'),
    path('profile/completion/update/', views.update_profile_completion, name='update_profile_completion'),

    # User Search and Listing
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/portfolio/', views.get_user_public_portfolio, name='user_public_portfolio'),

    # Education Management
    path('profile/education/', views.UserEducationListCreateView.as_view(), name='education_list_create'),
    path('profile/education/<int:pk>/', views.UserEducationDetailView.as_view(), name='education_detail'),

    # Experience Management
    path('profile/experience/', views.UserExperienceListCreateView.as_view(), name='experience_list_create'),
    path('profile/experience/<int:pk>/', views.UserExperienceDetailView.as_view(), name='experience_detail'),

    # Certification Management
    path('profile/certifications/', views.UserCertificationListCreateView.as_view(), name='certification_list_create'),
    path('profile/certifications/<int:pk>/', views.UserCertificationDetailView.as_view(), name='certification_detail'),

    # Portfolio Management
    path('profile/portfolio/', views.UserPortfolioListCreateView.as_view(), name='portfolio_list_create'),
    path('profile/portfolio/<int:pk>/', views.UserPortfolioDetailView.as_view(), name='portfolio_detail'),

    # Social Links Management
    path('profile/social-links/', views.UserSocialLinkListCreateView.as_view(), name='social_links_list_create'),
    path('profile/social-links/<int:pk>/', views.UserSocialLinkDetailView.as_view(), name='social_links_detail'),

    # Admin Views
    path('admin/users/', views.get_all_users, name='admin_all_users'),
    path('admin/users/assign-group/', views.assign_user_group, name='admin_assign_group'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='admin_toggle_user_status'),
    path('admin/stats/', views.get_user_stats, name='admin_user_stats'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)