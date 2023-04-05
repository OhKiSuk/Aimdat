"""
@modified at 2023.03.12
@author OKS in Aimdat Team
"""
from django.db import models
from services.models.inquiry import Inquiry
from tinymce.models import HTMLField

# Create your models here.
class InquiryAnswer(models.Model):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='answer')
    email = models.EmailField(max_length=255)
    content = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True)