"""
@created at 2023.02.28
@author OKS in Aimdat Team

@modified at 2023.04.11
@author OKS in Aimdat Team
"""
from datetime import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from ..models import User

class UserCreationForm(UserCreationForm):
    """
    사용자 생성 Form
    """
    email = forms.EmailField(required=True, error_messages={'required': '이메일을 입력하세요.'})
    password1 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '비밀번호를 입력하세요.'})
    password2 = forms.CharField(required=True, widget=forms.PasswordInput, error_messages={'required': '비밀번호 확인을 입력하세요.'})
    is_not_teen = forms.BooleanField(required=True, error_messages={'required': '만 14세 이상만 회원가입이 가능합니다.'})
    terms_of_use_agree = forms.BooleanField(required=True, error_messages={'required': '서비스 이용약관에 동의하지 않으면 가입할 수 없습니다.'})
    terms_of_privacy_agree = forms.BooleanField(required=True, error_messages={'required': '개인정보처리방침에 동의하지 않으면 가입할 수 없습니다.'})
    pin = forms.CharField(max_length=6, validators=[RegexValidator(r'^\d{6}$', message='PIN번호가 올바르지 않습니다.')])
    error_messages = {
        'unique': ("이미 가입된 이메일입니다."),
        'invalid': ("유효한 이메일이 아닙니다."),
        'password_mismatch': ("비밀번호가 일치하지 않습니다."),
        'password_requirements': ("비밀번호는 8자리 이상, 영어 소문자, 대문자, 숫자, 특수문자가 포함되어야 합니다.")
    }

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'is_not_teen', 'terms_of_use_agree', 'terms_of_privacy_agree', 'pin')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError(self.error_messages['unique'])
        
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8 or \
                not any(char.isdigit() for char in password1) or \
                not any(char.isupper() for char in password1) or \
                not any(char.islower() for char in password1) or \
                not any(char in '~`!@#$%^&*()_-+={[}]|\:;"<,>.?/' for char in password1):
            raise forms.ValidationError(self.error_messages['password_requirements'])
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(self.error_messages['password_mismatch'])
        return password2
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.expiration_date = datetime(9999, 12, 31)
        user.set_password(self.cleaned_data["password1"])
        if commit and self.cleaned_data['terms_of_use_agree'] and self.cleaned_data['terms_of_privacy_agree'] and self.cleaned_data['is_not_teen']:
            user.save()
        return user