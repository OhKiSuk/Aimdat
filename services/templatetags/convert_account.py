"""
@created at 2023.05.30
@author OKS in Aimdat Team

@modified at 2023.07.28
@author OKS in Aimdat Team
"""
from django import template

register = template.Library()

@register.filter(name='convert_account')
def convert_account(obj):
    """
    영문으로 저장된 필드명을 한글로 번역 후 return
    """

    index_list = {
        'revenue':'매출액',
        'operating_profit':'영업이익',
        'net_profit':'당기순이익',
        'total_assets':'총자산',
        'total_debt':'총부채',
        'total_capital':'총자본',
        'operating_cash_flow':'영업활동현금흐름',
        'investing_cash_flow':'투자활동현금흐름',
        'financing_cash_flow':'재무활동현금흐름',
        'current_ratio':'유동비율',
        'quick_ratio':'당좌비율',
        'debt_ratio':'부채비율',
        'interest_coverage_ratio':'이자보상배율',
        'cost_of_sales_ratio':'매출원가율',
        'gross_profit_margin':'매출액총이익률',
        'operating_margin':'영업이익률',
        'net_profit_margin':'순이익률',
        'roic':'총자본영업이익률',
        'roe':'자기자본이익률',
        'roa' :'총자산순이익률',
        'total_assets_turnover':'총자산회전율',
        'inventory_turnover':'재고자산회전율',
        'accounts_receivables_turnover':'매출채권회전율',
        'accounts_payable_turnover':'매입채무회전율',
        'working_capital_requirement':'운전자본소요율(일)',
        'working_capital_once':'1회운전자본',
        'revenue_growth':'매출액성장률',
        'operating_profit_growth':'영업이익성장률',
        'net_profit_growth':'순이익성장률',
        'net_worth_growth':'자기자본증가율',
        'assets_growth':'총자산증가율',
        'dps':'주당배당금(원)',
        'dividend':'배당금총액',
        'dividend_ratio':'배당률',
        'dividend_payout_ratio':'배당성향',
        'per':'PER',
        'pbr':'PBR',
        'psr':'PSR',
        'eps':'EPS',
        'bps':'BPS',
        'ev_ebitda':'EV/EBITDA',
        'ev_ocf':'EV/OCF'
    }

    return index_list[obj]