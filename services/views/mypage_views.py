"""
@created at 2023.04.01
@author OKS in Aimdat Team
"""
from django.shortcuts import redirect
from django.views.generic import TemplateView

class MyPageView(TemplateView):
    template_name = 'services/mypage/mypage.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account:login')
        
        return super().dispatch(request, *args, **kwargs)
    