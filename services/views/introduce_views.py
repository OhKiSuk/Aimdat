"""
@created at 2023.03.31
@author OKS in Aimdat Team
"""
from django.views.generic import TemplateView

class IntroduceView(TemplateView):
    template_name = 'services/introduce.html'