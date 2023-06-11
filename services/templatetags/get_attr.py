"""
@created at 2023.03.30
@author JSU in Aimdat Team

@modified at 2023.06.09
@author OKS in Aimdat Team
"""
import math

from decimal import Decimal
from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, key):
    if math.isnan(obj[key]):
        return Decimal(0.00)
    else:
        return obj[key]