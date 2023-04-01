"""
@created at 2023.04.01
@author OKS in Aimdat Team
"""
from django.views.generic import TemplateView

class MyPageView(TemplateView):
    template_name = 'services/mypage/mypage.html'