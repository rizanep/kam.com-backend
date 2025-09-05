# # users/models.py
# from django.contrib.auth.models import AbstractUser
# from django.db import models
#
#
# class User(AbstractUser):
#     USER_TYPES = (
#         ('client', 'Client'),
#         ('freelancer', 'Freelancer'),
#     )
#
#     email = models.EmailField(unique=True)
#     user_type = models.CharField(max_length=20, choices=USER_TYPES)
#     phone_number = models.CharField(max_length=15, blank=True)
#     profile_picture = models.ImageField(upload_to='profiles/', blank=True)
#     bio = models.TextField(blank=True)
#     skills = models.JSONField(default=list, blank=True)  # For freelancers
#     company_name = models.CharField(max_length=100, blank=True)  # For clients
#
#     # Email verification
#     is_verified = models.BooleanField(default=False)
#     verification_token = models.CharField(max_length=100, blank=True)
#
#     # Security fields
#     last_login_ip = models.GenericIPAddressField(blank=True, null=True)
#     mfa_enabled = models.BooleanField(default=False)
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']
#
#     def __str__(self):
#         return f"{self.email} ({self.user_type})"


from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class User(AbstractUser):
    USER_TYPES = (
        ('client', 'Client'),
        ('freelancer', 'Freelancer'),
        ('admin', 'Admin'),
    )

    EXPERIENCE_LEVELS = (
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
        ('senior', 'Senior'),
    )

    AVAILABILITY_STATUS = (
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('unavailable', 'Unavailable'),
    )

    TIMEZONE_CHOICES = (
        ('UTC', 'UTC'),
        ('America/New_York', 'Eastern Time'),
        ('America/Chicago', 'Central Time'),
        ('America/Denver', 'Mountain Time'),
        ('America/Los_Angeles', 'Pacific Time'),
        ('Europe/London', 'London'),
        ('Europe/Berlin', 'Berlin'),
        ('Asia/Tokyo', 'Tokyo'),
        ('Asia/Shanghai', 'Shanghai'),
        ('Asia/Kolkata', 'India Standard Time'),
        # Add more as needed
    )

    # Basic Information
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    bio = models.TextField(blank=True, max_length=1000)

    # Location Information
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')

    # Professional Information
    title = models.CharField(max_length=100, blank=True)  # Job title/profession
    company_name = models.CharField(max_length=100, blank=True)  # For clients
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Skills and Experience (Primarily for freelancers)
    skills = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    languages_spoken = models.JSONField(default=list, blank=True)  # ['English', 'Spanish', etc.]

    # Freelancer-specific fields
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')  # Currency code
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS, default='available')
    availability_hours_per_week = models.PositiveIntegerField(null=True, blank=True)

    # Rating and Reviews
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    total_projects_completed = models.PositiveIntegerField(default=0)

    # Client-specific fields
    company_size = models.CharField(max_length=50, blank=True)  # 'startup', 'small', 'medium', 'large'
    industry = models.CharField(max_length=100, blank=True)
    total_projects_posted = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Email verification and security
    is_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    phone_verified = models.BooleanField(default=False)
    identity_verified = models.BooleanField(default=False)  # For freelancers

    # Security fields
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    # Profile completion and activity
    profile_completion_percentage = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)  # For promoted profiles
    is_premium = models.BooleanField(default=False)  # Premium membership
    premium_expires = models.DateTimeField(null=True, blank=True)

    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    privacy_settings = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['user_type', 'is_active']),
            models.Index(fields=['average_rating', 'total_reviews']),
            models.Index(fields=['availability_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.email} ({self.user_type})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_freelancer(self):
        return self.user_type == 'freelancer'

    @property
    def is_client(self):
        return self.user_type == 'client'

    @property
    def is_account_locked(self):
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False

    def calculate_profile_completion(self):
        """Calculate profile completion percentage"""
        fields_to_check = [
            'first_name', 'last_name', 'bio', 'phone_number', 'profile_picture',
            'country', 'city', 'title'
        ]

        if self.is_freelancer:
            fields_to_check.extend([
                'skills', 'experience_level', 'hourly_rate', 'portfolio_url'
            ])
        else:  # client
            fields_to_check.extend([
                'company_name', 'company_size', 'industry'
            ])

        completed_fields = 0
        for field in fields_to_check:
            value = getattr(self, field, None)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    completed_fields += 1
                elif not isinstance(value, list):
                    completed_fields += 1

        percentage = int((completed_fields / len(fields_to_check)) * 100)
        self.profile_completion_percentage = percentage
        return percentage

    def update_rating(self, new_rating):
        """Update average rating when a new review is added"""
        total_rating_points = self.average_rating * self.total_reviews
        total_rating_points += new_rating
        self.total_reviews += 1
        self.average_rating = total_rating_points / self.total_reviews
        self.save(update_fields=['average_rating', 'total_reviews'])

    def can_login(self):
        """Check if user can login (not locked)"""
        return not self.is_account_locked and self.is_active

    def reset_login_attempts(self):
        """Reset login attempts after successful login"""
        self.login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['login_attempts', 'last_failed_login'])

    def increment_login_attempts(self):
        """Increment login attempts and lock account if needed"""
        self.login_attempts += 1
        self.last_failed_login = timezone.now()

        # Lock account for 30 minutes after 5 failed attempts
        if self.login_attempts >= 5:
            self.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)

        self.save(update_fields=['login_attempts', 'last_failed_login', 'account_locked_until'])


class UserEducation(models.Model):
    """Education history for users (mainly freelancers)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    institution = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if currently studying
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class UserExperience(models.Model):
    """Work experience for users (mainly freelancers)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experience')
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=100, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if current job
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} at {self.company}"


class UserCertification(models.Model):
    """Certifications for users (mainly freelancers)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"


class UserPortfolio(models.Model):
    """Portfolio items for freelancers"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='portfolio/', blank=True)
    url = models.URLField(blank=True)
    technologies_used = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.email}"


class UserSocialLink(models.Model):
    """Social media links for users"""
    PLATFORM_CHOICES = (
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('dribbble', 'Dribbble'),
        ('behance', 'Behance'),
        ('facebook', 'Facebook'),
        ('youtube', 'YouTube'),
        ('website', 'Personal Website'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'platform']

    def __str__(self):
        return f"{self.user.email} - {self.platform}"