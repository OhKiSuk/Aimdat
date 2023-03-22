"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.03.19
@author JSU in Aimdat Team
"""
from django.db import models
from .corp_id import CorpId

class CorpSummaryFinancialStatements(models.Model):
    corp_id = models.ForeignKey(CorpId, on_delete=models.CASCADE, related_name='corp_summary')
    disclosure_date = models.DateField() #공시일
    year = models.CharField(max_length=4) #년도
    month = models.CharField(max_length=2) #월
    revenue = models.DecimalField(max_digits=19, decimal_places=2, null=True) #매출액
    operating_profit = models.DecimalField(max_digits=19, decimal_places=2, null=True) #영업이익
    net_profit = models.DecimalField(max_digits=19, decimal_places=2, null=True) #당기순이익
    operating_margin = models.DecimalField(max_digits=19, decimal_places=2, null=True) #영업이익률
    net_profit_margin = models.DecimalField(max_digits=19, decimal_places=2, null=True) #순이익률
    debt_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) #부채비율
    cost_of_sales_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) #매출원가율
    quick_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) #당좌비율
    dividend = models.DecimalField(max_digits=19, decimal_places=2, null=True) #배당금
    total_dividend = models.DecimalField(max_digits=19, decimal_places=2, null=True) #배당금 총액
    dividend_yield = models.DecimalField(max_digits=19, decimal_places=2, null=True) #배당 수익률
    dividend_payout_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) #배당성향
    dividend_ratio = models.DecimalField(max_digits=19, decimal_places=2, null=True) #배당률
    per = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주가수익비율
    pbr = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주가순자산비율
    psr = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주가매출비율
    ev_ebitda = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주식 시가총액+순부채/이자비용, 법인세, 유무형자산 감가상각비를 반영하기 전의 이익
    ev_per_ebitda = models.DecimalField(max_digits=19, decimal_places=2, null=True)
    eps = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주당 순이익
    bps = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주당 장부가치
    roe = models.DecimalField(max_digits=19, decimal_places=2, null=True) #자기자본이익률
    dps = models.DecimalField(max_digits=19, decimal_places=2, null=True) #주당 배당금
    total_dept = models.DecimalField(max_digits=19, decimal_places=2, null=True) #총 부채
    total_asset = models.DecimalField(max_digits=19, decimal_places=2, null=True) #총 자산
    total_capital = models.DecimalField(max_digits=19, decimal_places=2, null=True) #총 자본
    borrow_debt = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 총 차입금
    face_value = models.DecimalField(max_digits=19, decimal_places=2, null=True) # 액면가