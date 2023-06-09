"""
@created at 2023.06.02
@author OKS in Aimdat Team

@modified at 2023.06.08
@author OKS in Aimdat Team
"""
import math

from django import template

register = template.Library()

@register.filter(name='get_index_field_data')
def get_index_field_data(obj, field):
    """
    InvestmentIndex에 저장된 데이터 획득
    """
    try: 
        if obj[field] != None:
            if math.isnan(obj[field]):
                return 0
            else:
                return int(obj[field])
        else:
            return 0
    except:
        if getattr(obj, field) != None:
            if math.isnan(getattr(obj, field)):
                return 0
            else:
                return int(getattr(obj, field))
        else:
            return 0