"""
@created at 2023.03.12
@author OKS in Aimdat Team
"""
from admin_dashboard.models import InquiryAnswer
from bleach.sanitizer import Cleaner
from django.forms import CharField, ModelForm
from tinymce.widgets import TinyMCE

class InquiryAnswerForm(ModelForm):
    content = CharField(label='', widget=TinyMCE(attrs={'selector': 'textarea#id_content'}))

    class Meta:
        model = InquiryAnswer
        fields = ('content',)

    def clean_content(self):
        content = self.cleaned_data['content']
        
        cleaner = Cleaner(
            tags=['b', 'blockquote', 'br', 'del', 'em', 'h1', 'h2', 'h3', 'i', 'p', 'pre', 'sup', 'sub', 'strong', 'strike'],
            attributes={'*': ['class', 'style']},
            strip=True,
            strip_comments=True
        )

        return cleaner.clean(content)