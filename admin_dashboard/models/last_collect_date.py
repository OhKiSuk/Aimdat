"""
@created at 2023.04.05
@author cslee in Aimdat Team
"""
from django.db import models

# Create your models here.
class LastCollectDate(models.Model):
    last_corp_collect_date = models.DateField()
    last_stock_collect_date = models.DateField()
    last_summaryfs_collect_date = models.DateField()