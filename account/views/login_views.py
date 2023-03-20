"""
@created at 2023.03.01
@author OKS in Aimdat Team

@modified at 2023.03.19
@author OKS in Aimdat Team
"""
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..backends import EmailBackend

class ServiceLoginView(LoginView):
    """
    서비스 로그인 뷰
    """
    template_name = 'account/login.html'
    success_url = reverse_lazy('account:signup')
    authentication_form = AuthenticationForm
    backend = EmailBackend

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account:signup')
        
        return super().dispatch(request, *args, **kwargs)