from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone as django_timezone


class CustomUserManager(BaseUserManager):
    """Manager for custom user model"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as username and role-based fields
    """
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True
    )
    
    # User information
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    
    # Role flags
    is_admin = models.BooleanField(
        default=False,
        help_text='Admin users can view all signals and manage system settings'
    )
    is_trader = models.BooleanField(
        default=True,
        help_text='Trader users can only see their own signals'
    )
    
    # Timezone for user
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text='User timezone (e.g., America/New_York, Europe/London)'
    )
    
    # API Key for webhook authentication
    api_key = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='API key for TradingView webhook authentication'
    )
    
    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=django_timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Return the user's short name"""
        return self.first_name or self.email.split('@')[0]
    
    def generate_api_key(self):
        """Generate a unique API key for the user"""
        import secrets
        self.api_key = secrets.token_urlsafe(48)
        self.save(update_fields=['api_key'])
        return self.api_key
    
    @property
    def role(self):
        """Return user's role as string"""
        if self.is_superuser:
            return 'Superuser'
        elif self.is_admin:
            return 'Admin'
        elif self.is_trader:
            return 'Trader'
        return 'User'
