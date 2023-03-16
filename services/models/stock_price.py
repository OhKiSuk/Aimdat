"""
@created at 2023.03.15
@author OKS in Aimdat Team
"""
from django.db import models
from .corp_id import CorpId

class StockPrice(models.Model):
    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='corp_id')
    trade_date = models.DateField()
    open_price = models.DecimalField(max_digits=16, decimal_places=6)
    high_price = models.DecimalField(max_digits=16, decimal_places=6)
    low_price = models.DecimalField(max_digits=16, decimal_places=6)
    close_price = models.DecimalField(max_digits=16, decimal_places=6)
    low_price_52 = models.DecimalField(max_digits=16, decimal_places=6)
    high_price_52 = models.DecimalField(max_digits=16, decimal_places=6)
    total_stock = models.DecimalField(max_digits=16, decimal_places=6)
    market_capitalization = models.DecimalField(max_digits=19, decimal_places=2)