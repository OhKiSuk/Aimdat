"""
@created at 2023.04.03
@author OKS in Aimdat Team
"""
from bleach.sanitizer import Cleaner
from django import forms
from django.core.exceptions import ValidationError
from tinymce.widgets import TinyMCE

from ..models.inquiry import Inquiry

class AddInquiryForm(forms.ModelForm):
    title = forms.CharField(label=False, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목'}) ,error_messages={'required': '제목을 입력해주세요.'})
    inquiry_category = forms.ChoiceField(
        label=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        choices=[('choices', '문의유형 선택'), ('account', '계정 관련'), ('service', '서비스 이용 관련'), ('report', '버그/오류 신고')],
        error_messages={'required': '문의유형을 선택하세요.', 'invalid_choice': '잘못된 입력입니다.'})
    content = forms.CharField(label='', widget=TinyMCE(attrs={'selector': 'textarea#id_content'}), error_messages={'required': '문의내용을 입력하세요.'})

    class Meta:
        model = Inquiry
        fields = ('title', 'inquiry_category', 'content',)

    def clean_inquiry_category(self):
        inquiry_category = self.cleaned_data.get('inquiry_category')

        if inquiry_category == 'choices':
            raise ValidationError('문의유형을 선택하세요.')
        elif inquiry_category not in ['account', 'service', 'report']:
            raise ValidationError('잘못된 입력입니다.')
        return inquiry_category

    def clean_content(self):
        content = self.cleaned_data['content']
        
        cleaner = Cleaner(
            tags=['b', 'blockquote', 'br', 'del', 'em', 'h1', 'h2', 'h3', 'i', 'p', 'pre', 'sup', 'sub', 'strong', 'strike'],
            attributes={'*': ['class', 'style']},
            strip=True,
            strip_comments=True
        )

        return cleaner.clean(content)