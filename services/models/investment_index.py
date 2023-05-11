"""
@created at 2023.05.10
@author JSU in Aimdat Team
"""
from django.db import models

from .corp_id import CorpId

class InvestmentIndex(models.Model):
    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='investment_index')
    year = models.CharField(max_length=4)
    quarter = models.CharField(max_length=2)
    revenue = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 매출액(영업수익)
    cost_of_sales = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 매출원가(영업비용)
    operating_profit = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 영업이익
    net_profit = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 당기순이익
    inventories = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 재고자산
    total_debt = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 총부채
    total_asset = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 총자산
    total_capital = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 총자본
    current_asset = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 유동자산
    current_liability = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 유동부채
    cash_and_cash_equivalents = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 현금성자산
    interest_expense = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 이자비용
    corporate_tax = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 법인세비용
    depreciation_cost = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 감가상각비
    cash_flows_from_operating = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 현금흐름(영업활동)
    cash_flows_from_investing_activities = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 현금흐름(투자활동)
    total_dividend = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 총배당금

    # 계산 후 저장되는 값
    cost_of_sales_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 매출원가율
    operating_margin = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 영업이익률
    net_profit_margin = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 순이익률
    roe = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    roa = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    current_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 유동비율
    quick_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 당좌비율
    debt_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 부채비율
    per = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    pbr = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    psr = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    eps = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    bps = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    dps = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 주당배당금
    ev_ebitda = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    ev_ocf = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    dividend_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 배당률
    payout_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 배당성향


