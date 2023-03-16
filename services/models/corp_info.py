"""
@created at 2023.03.15
@author OKS in Aimdat Team
"""
from django.db import models
from .corp_id import CorpId

class CorpInfo(models.Model):
    corp_id = models.OneToOneField(CorpId, models.CASCADE, related_name='corp_info')
    corp_homepage_url = models.URLField(null=True)
    corp_settlement_date = models.DateField()
    corp_ceo_name = models.CharField(max_length=255, null=True)
    corp_summary = models.TextField(null=True)