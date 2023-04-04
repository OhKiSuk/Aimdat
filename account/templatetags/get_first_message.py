"""
@created at 2023.04.05
@author OKS in Aimdat Team
"""
from django import template

register = template.Library()

@register.filter(name='get_first_message')
def get_first_message(messages):
    return list(messages)[0]