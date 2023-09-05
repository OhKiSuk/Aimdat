"""
@created at 2023.07.09
@author OKS in Aimdat Team

@modified at 2023.08.25
@author OKS in Aimdat Team
"""
from decimal import (
    Context,
    Decimal
)
from django import template

register = template.Library()

@register.filter(name='divide_marketcap')
def divide_marketcap(obj):
    ctx = Context(prec=11)

    obj_to_decimal = Decimal(obj)

    if obj_to_decimal >= Decimal(1_000_000_000_000):
        result = ctx.divide(obj_to_decimal, Decimal(1_000_000_000_000))
        trillion = str(result).split('.')[0]
        billion = str(result).split('.')[1][0:4]

        if int(billion) < 1:
            return trillion+'조'
        else:
            return trillion+'조 '+billion+'억'
    elif obj_to_decimal >= Decimal(100_000_000):
        result = ctx.divide(obj_to_decimal, Decimal(100_000_000))
        billion = str(result).split('.')[0]

        return billion+'억'
    else:
        return obj_to_decimal