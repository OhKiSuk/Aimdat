"""
@created at 2023.08.16
@author OKS in Aimdat Team
"""
from django.db import models

from ..models.corp_id import CorpId

class ReitsInquiry(models.Model):
    corp_id = models.OneToOneField(CorpId, on_delete=models.CASCADE, related_name='reits_inquiry')
    establishment_date = models.DateField() # 설립일
    listing_date = models.DateField() # 상장일
    settlement_cycle = models.CharField(max_length=255) # 결산월
    investment_assets_info = models.JSONField(default={}) # 투자자산 정보
    borrowed_info = models.JSONField(default={}) # 차입금 정보
    lastest_dividend_date = models.DateField(null=True) # 최근 배당일
    lastest_dividend_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True) # 최근 배당률
    update_date = models.DateField(auto_now=True) # 정보 갱신일