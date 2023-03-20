"""
@created at 2023.03.01
@author OKS in Aimdat Team

@modified at 2023.03.19
@author OKS in Aimdat Team
"""
from axes.backends import AxesBackend
from .models import User

class EmailBackend(AxesBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None