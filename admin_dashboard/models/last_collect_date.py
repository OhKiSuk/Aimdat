"""
@created at 2023.04.05
@author cslee in Aimdat Team

@modified at 2023.05.16
@author OKS in Aimdat Team
"""
from django.db import models

class LastCollectDate(models.Model):
    """
        ##collect_type 목록##

        corp_info: 기업 정보 수집
        stock_price: 주가 정보 수집
        fcorp_fs: 금융기업 재무제표
        dcorp_fs: 비금융기업 재무제표
        investment_index: 투자지표
    """
    collect_user = models.CharField(max_length=255) # 수집한 관리자 메일명
    collect_type = models.CharField(max_length=255) # 수집한 데이터 종류
    collect_date = models.DateTimeField(auto_now=True) # 기업정보 수집일