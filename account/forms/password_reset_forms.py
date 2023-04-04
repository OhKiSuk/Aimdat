"""
@created at 2023.03.04
@author OKS in Aimdat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
from django import forms
from django.contrib.auth.forms import (
    PasswordResetForm, 
    SetPasswordForm
)
from django.core.exceptions import ValidationError

from ..models import User

class CustomPasswordResetForm(PasswordResetForm):
    """
    패스워드 초기화 페이지 폼
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput)
    
    class Meta:
        fields = ('email')
        
    def get_users(self, email=''):
        email = self.cleaned_data.get('email')

        active_users = User.objects.filter(**{
            'email__iexact': email,
            'is_active': True
        })

        return (
            u for u in active_users if u.has_usable_password()
        )
    
class CustomSetPasswordForm(SetPasswordForm):
    """
    패스워드 초기화 확인 폼
    """
    new_password1 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '비밀번호를 입력하세요.'})
    new_password2 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '비밀번호 확인을 입력하세요.'})

    error_messages = {
        'password_mismatch': ("비밀번호가 일치하지 않습니다."),
        'password_requirements': ("비밀번호는 8자리 이상, 영어 소문자, 대문자, 숫자, 특수문자가 포함되어야 합니다.")
    }

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if len(new_password1) < 8 or \
                not any(char.isdigit() for char in new_password1) or \
                not any(char.isupper() for char in new_password1) or \
                not any(char.islower() for char in new_password1) or \
                not any(char in '~`!@#$%^&*()_-+={[}]|\:;"<,>.?/' for char in new_password1):
            raise forms.ValidationError(self.error_messages['password_requirements'])
        return new_password1
    
    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError(self.error_messages['password_mismatch'])
        return new_password2