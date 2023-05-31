"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.05.30
@author OKS in Aimdat Team
"""
from django.db import models
from .corp_id import CorpId

class StockPrice(models.Model):
    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='corp_id')
    trade_date = models.CharField(max_length=255) # 거래기준일
    open_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 시가
    high_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 고가
    low_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 저가
    close_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 종가
    total_stock = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 총주식수
    market_capitalization = models.DecimalField(max_digits=20, decimal_places=2 ,null=True) # 시가총액
    trade_quantity = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 거래량
    trade_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 거래대금
    change_price = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 전일가대비금액
    change_rate = models.DecimalField(max_digits=20, decimal_places=6 ,null=True) # 전일가대비비율
        
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['corp_id', 'trade_date'],
                name='unique trade_date'
            )
        ]
    