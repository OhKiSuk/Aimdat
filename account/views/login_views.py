"""
@created at 2023.03.01
@author OKS in Aimdat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from ..backends import EmailBackend
from ..forms.login_forms import CustomAuthenticationForm

class ServiceLoginView(UserPassesTestMixin, LoginView):
    """
    서비스 로그인 뷰
    """
    template_name = 'account/login.html'
    success_url = reverse_lazy('index')
    authentication_form = CustomAuthenticationForm
    backend = EmailBackend

    def test_func(self):
        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):
        if self.request.user.is_admin:
            return HttpResponseRedirect(reverse_lazy('admin:logout'))
        return HttpResponseRedirect(reverse_lazy('index'))