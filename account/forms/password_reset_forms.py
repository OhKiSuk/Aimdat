"""
@created at 2023.03.04
@author OKS in Aimdat Team
"""

from django import forms

class ResetPasswordForm(forms.Form):
    """
    패스워드 초기화 페이지 폼
    """
    email = forms.EmailField(required=True)
    
    class Meta:
        fields = ('email')