"""
@created at 2023.03.30
@author OKS in Aimdat Team
"""
from django.views.generic import TemplateView

class TermsOfUseView(TemplateView):
    template_name = 'services/terms/terms_of_use.html'

class TermsOfPrivacyView(TemplateView):
    template_name = 'services/terms/terms_of_privacy.html'