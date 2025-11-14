from django.contrib.auth.backends import ModelBackend
from .models import CustomUser


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that uses email instead of username
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        """Authenticate user by email and password"""
        if email is None or password is None:
            return None
        
        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except CustomUser.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            CustomUser().set_password(password)
        
        return None
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
