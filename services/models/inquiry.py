"""
@created at 2023.03.12
@author OKS in Aimdat Team
"""
from django.db import models
from tinymce.models import HTMLField

# Create your models here.
class Inquiry(models.Model):
    email = models.EmailField(max_length=255)
    title = models.CharField(max_length=255)
    inquiry_category = models.CharField(max_length=255)
    content = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True)