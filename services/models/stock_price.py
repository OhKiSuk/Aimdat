"""
@created at 2023.03.15
@author OKS in Aimdat Team
"""
from django.db import models
from .corp_id import CorpId

class StockPrice(models.Model):
    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='corp_id')
    trade_date = models.DateField() # 거래기준일
    open_price = models.DecimalField(max_digits=16, decimal_places=6) # 시가
    high_price = models.DecimalField(max_digits=16, decimal_places=6) # 고가
    low_price = models.DecimalField(max_digits=16, decimal_places=6) # 저가
    close_price = models.DecimalField(max_digits=16, decimal_places=6) # 종가
    low_price_52 = models.DecimalField(max_digits=16, decimal_places=6) # 52주 저가
    high_price_52 = models.DecimalField(max_digits=16, decimal_places=6) # 52주 고가
    total_stock = models.DecimalField(max_digits=16, decimal_places=6) # 총주식수
    market_capitalization = models.DecimalField(max_digits=19, decimal_places=2) # 시가총액
    trade_quantity = models.DecimalField(max_digits=16, decimal_places=6) # 거래량
    trade_price = models.DecimalField(max_digits=16, decimal_places=6) # 거래대금
    change_price = models.DecimalField(max_digits=16, decimal_places=6) # 전일가대비금액
    change_rate = models.DecimalField(max_digits=16, decimal_places=6) # 전일가대비비율