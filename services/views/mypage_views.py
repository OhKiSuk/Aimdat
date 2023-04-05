"""
@created at 2023.04.01
@author OKS in Aimdat Team

@modified at 2023.04.05
@author OKS in Aimdat Team
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView

class MyPageView(UserPassesTestMixin, TemplateView):
    template_name = 'services/mypage/mypage.html'
    login_url = reverse_lazy('account:login')
    redirect_field_name=None

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated