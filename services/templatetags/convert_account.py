"""
@created at 2023.05.30
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
        'revenue': '매출액',
        'operating_profit': '영업이익',
        'net_profit': '당기순이익',
        'cost_of_sales': '매출원가',
        'cost_of_sales_ratio': '매출원가율',
        'operating_margin': '영업이익률',
        'net_profit_margin': '순이익률',
        'roe': 'ROE',
        'roa': 'ROA',
        'current_ratio': '유동비율',
        'quick_ratio': '당좌비율',
        'debt_ratio': '부채비율',
        'per': 'PER',
        'pbr': 'PBR',
        'psr': 'PSR',
        'eps': 'EPS',
        'bps': 'BPS',
        'ev_ebitda': 'EV/EBITDA',
        'ev_ocf': 'EV/OCF',
        'dividend': '배당금',
        'dividend_ratio': '배당률',
        'dividend_payout_ratio': '배당성향',
        'dps': 'DPS'
    }

    return index_list[obj]