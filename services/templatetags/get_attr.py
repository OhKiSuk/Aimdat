"""
@created at 2023.03.30
@author JSU in Aimdat Team
"""
from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, attr):
    return obj[attr]