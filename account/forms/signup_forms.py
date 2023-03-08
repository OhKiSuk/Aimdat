"""
@created at 2023.02.28
@author OKS in Aimdat Team
"""

from django import forms

from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from ..models import User

class UserCreationForm(UserCreationForm):
    """
    사용자 생성 Form
    """
    email = forms.EmailField(required=True)
    terms_of_use_agree = forms.BooleanField(required=True)
    terms_of_privacy_agree = forms.BooleanField(required=True)
    pin = forms.CharField(max_length=6, validators=[RegexValidator(r'^\d{6}$', message='6자리의 숫자만 입력하세요.')])

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'terms_of_use_agree', 'terms_of_privacy_agree', 'pin')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("이미 가입된 이메일입니다.")
        
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("패스워드가 일치하지 않습니다.")
        return password2
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit and self.cleaned_data['terms_of_use_agree'] and self.cleaned_data['terms_of_privacy_agree']:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    """
    사용자 정보 변경 Form
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email',)