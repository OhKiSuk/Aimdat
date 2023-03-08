"""
@created at 2023.02.28
@author OKS in Aimdat Team
"""

from django import forms

class SendPinForm(forms.Form):
    """
    PIN 전송 폼
    """
    email = forms.EmailField(required=True)
    
    class Meta:
        fields = ('email')