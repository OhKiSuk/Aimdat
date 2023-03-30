"""
@created at 2023.03.30
@author OKS in Aimdat Team
"""
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
    
class CustomPasswordChangeForm(PasswordChangeForm):
    """
    패스워드 초기화 확인 폼
    """
    old_password = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '기존 비밀번호를 입력하세요.'})
    new_password1 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '새 비밀번호를 입력하세요.'})
    new_password2 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '새 비밀번호 확인을 입력하세요.'})

    error_messages = {
        'password_incorrect': _("기존 비밀번호가 올바르지 않습니다."),
        'password_mismatch': _("비밀번호가 일치하지 않습니다."),
        'password_requirements': _("비밀번호는 8자리 이상, 영어 소문자, 대문자, 숫자, 특수문자가 포함되어야 합니다.")
    }

    def clean_old_password(self):
        """
        기존 비밀번호 일치 여부 검증
        """
        old_password = self.cleaned_data.get('old_password')
        if check_password(self.user.password, old_password):
            raise ValidationError(self.error_messages['password_incorrect'])
        return old_password

    def clean_password1(self):
        """
        비밀번호 규칙을 준수하는 지 검증
        """
        new_password1 = self.cleaned_data.get('new_password1')
        if len(new_password1) < 8 or \
                not any(char.isdigit() for char in new_password1) or \
                not any(char.isupper() for char in new_password1) or \
                not any(char.islower() for char in new_password1) or \
                not any(char in '~`!@#$%^&*()_-+={[}]|\:;"<,>.?/' for char in new_password1):
            raise forms.ValidationError(self.error_messages['password_requirements'])
        return new_password1
    
    def clean_password2(self):
        """
        비밀번호 및 비밀번호 확인 값이 일치하는 지 검증
        """
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError(self.error_messages['password_mismatch'])
        return new_password2