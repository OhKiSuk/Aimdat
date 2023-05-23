"""
@created at 2023.03.26
@author OKS in Aimdat Team

@modified at 2023.05.23
@author OKS in Aimdat Team
"""
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

from ..models import User

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(error_messages={'required': '이메일을 입력하세요.'})
    password = forms.CharField(widget=forms.PasswordInput, error_messages={'required': '패스워드를 입력하세요.'})

    error_messages = {
        'invalid_login': ("이메일, 패스워드가 일치하지 않습니다."),
        'inactive': ("유효한 계정이 아닙니다. 고객센터에 문의하세요."),
    }

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise ValidationError(self.error_messages['inactive'])
        
        # 서비스 로그인에서 관리자 계정으로 로그인 시도 시 에러
        if not '/admin/' in self.request.path_info:
            if User.objects.filter(email=user.get_username()).exists():
                if User.objects.get(email=user.get_username()).is_admin:
                    raise ValidationError(self.error_messages['invalid_login'])