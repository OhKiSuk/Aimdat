"""
@created at 2023.03.30
@author JSU in Aimdat Team

@modified at 2023.05.28
@author OKS in Aimdat Team
"""
from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, key):
    """
    한국어로 저장된 필드명을 영문으로 전환 후 return
    """

    index_list = {
        '매출액': 'revenue',
        '영업이익': 'operating_profit',
        '당기순이익': 'net_profit',
        '매출원가': 'cost_of_sales',
        '매출원가율': 'cost_of_sales_ratio',
        '영업이익률': 'operating_margin',
        '순이익률': 'net_profit_margin',
        'ROE': 'roe',
        'ROA': 'roa',
        '유동비율': 'current_ratio',
        '당좌비율': 'quick_ratio',
        '부채비율': 'debt_ratio',
        'PER': 'per',
        'PBR': 'pbr',
        'PSR': 'psr',
        'EPS': 'eps',
        'BPS': 'bps',
        'EV/EBITDA': 'ev_ebitda',
        'EV/OCF': 'ev_ocf',
        '배당금': 'dividend',
        '배당률': 'dividend_ratio',
        '배당성향': 'dividend_payout_ratio',
        'DPS': 'dps'
    }

    for index in index_list.keys():
        if key == index:
            return str(obj[index_list[key]])