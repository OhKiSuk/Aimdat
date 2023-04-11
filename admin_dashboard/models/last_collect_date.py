"""
@modified at 2023.04.05
@author cslee in Aimdat Team
"""
from datetime import datetime
from django.db import models
# Create your models here.
class LastCollectDate(models.Model):
    default_day = datetime(2020, 1, 1)
    last_corp_collect_date = models.DateField(default=default_day) # 마지막 기업정보 수집일
    last_stock_collect_date = models.DateField(default=datetime.today().date()) # 마지막 주식정보 수집일
    last_summaryfs_collect_date = models.DateField(default=default_day) # 마지막 재무정보 수집일