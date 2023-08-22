"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.05.23
@author OKS in Aimdat Team
"""
from django.db import models

class CorpId(models.Model):
    corp_name = models.CharField(max_length=255) #기업명
    corp_country = models.CharField(max_length=255, null=True) #소속 국가
    corp_market = models.CharField(max_length=255, null=True) #소속 시장(예: 코스피, 코스닥 등)
    corp_isin = models.CharField(max_length=255, null=True) #국제 증권 식별번호
    stock_code = models.CharField(max_length=255, null=True) #종목 코드
    corp_sectors = models.CharField(max_length=255, null=True) #소속 섹터(예: 제조업, 서비스업 등)
    base_date = models.DateField(null=True) # 정보 기준일
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['corp_name', 'corp_isin', 'stock_code'],
                name='unique corp'
            )
        ]

    def __str__(self):
        return self.corp_name