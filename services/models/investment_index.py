"""
@created at 2023.05.10
@author JSU in Aimdat Team

@modified at 2023.10.16
@author OKS in Aimdat Team
"""
from django.db import models

from .corp_id import CorpId

class InvestmentIndex(models.Model):

    class Meta:
        unique_together = ['id', 'corp_id', 'year', 'quarter', 'fs_type']

    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='investment_index')
    year = models.CharField(max_length=4)
    quarter = models.CharField(max_length=2)
    fs_type = models.CharField(max_length=1) # {연결: 0, 별도: 5}
    settlement_date = models.CharField(max_length=255, null=True) # 결산일

    # 계정과목 정보
    revenue = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매출액(영업수익)
    operating_profit = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 영업이익
    net_profit = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 당기순이익
    total_assets = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자산
    total_debt = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총부채
    total_capital = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자본
    operating_cash_flow = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 영업활동 현금흐름
    investing_cash_flow = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 투자활동 현금흐름
    financing_cash_flow = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 재무활동 현금흐름

    # 안정성
    current_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 유동비율
    quick_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 당좌비율
    debt_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 부채비율
    interest_coverage_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 이자보상배율

    # 수익성
    cost_of_sales_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매출원가율
    gross_profit_margin = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매출액총이익률
    operating_margin = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 영업이익률
    net_profit_margin = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 순이익률
    roic = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자본영업이익률
    roe = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 자기자본이익률
    roa = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자산순이익률

    # 활동성
    total_assets_turnover = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자산회전율
    inventory_turnover = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 재고자산회전율
    accounts_receivables_turnover = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매출채권회전율
    accounts_payable_turnover = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매입채무회전율
    working_capital_requirement = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 운전자본소요율(일)
    working_capital_once = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 1회 운전자본

    # 성장성
    revenue_growth = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 매출액성장률
    operating_profit_growth = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 영업이익성장률
    net_profit_growth = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 순이익성장률
    net_worth_growth = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 자기자본 증가율
    assets_growth = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 총자산증가율

    # 배당
    dps = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주당배당금
    dividend = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 배당금 총액
    dividend_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 배당률
    dividend_payout_ratio = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 배당성향

    # 투자지표
    per = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주가수익비율
    pbr = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주가순자산비율
    psr = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주가매출액비율
    eps = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주당 순이익
    bps = models.DecimalField(max_digits=30, decimal_places=6, null=True) # 주당 순자산가치
    ev_ebitda = models.DecimalField(max_digits=30, decimal_places=6, null=True) # EV/EBITDA
    ev_ocf = models.DecimalField(max_digits=30, decimal_places=6, null=True) # EV/OCF