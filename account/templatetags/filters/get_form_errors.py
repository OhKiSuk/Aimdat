"""
@created at 2023.03.26
@author OKS in Aimdat Team
"""
from django import template

register = template.Library()

@register.filter(name='get_form_errors')
def get_form_errors(values):
    return list(values)[0][0]