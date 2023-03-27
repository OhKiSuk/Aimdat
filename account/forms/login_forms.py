"""
@created at 2023.03.26
@author OKS in Aimdat Team
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(error_messages={'required': '이메일을 입력하세요.'})
    password = forms.CharField(widget=forms.PasswordInput, error_messages={'required': '패스워드를 입력하세요.'})

    error_messages = {
        'invalid_login': ("이메일, 패스워드가 일치하지 않습니다."),
        'inactive': ("유효한 계정이 아닙니다. 고객센터에 문의하세요."),
    }