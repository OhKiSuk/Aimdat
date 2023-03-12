"""
@created at 2023.03.11
@author OKS in Aimdat Team
"""
from account.models import User
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError

class AdminCreationForm(UserCreationForm):
    """
    관리자 생성 Form
    """
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

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
        if commit:
            user.save()
        return user
    
class AdminChangeForm(UserChangeForm):
    """
    관리자 정보 변경 Form
    """
    password = ReadOnlyPasswordHashField()

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'password')