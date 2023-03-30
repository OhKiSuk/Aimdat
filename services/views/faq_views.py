"""
@created at 2023.03.30
@author OKS in Aimdat Team
"""
from django.views.generic import TemplateView

class FaqView(TemplateView):
    template_name = 'services/faq.html'