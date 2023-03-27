"""
@created at 2023.03.01
@author OKS in Aimdat Team

@modified at 2023.03.19
@author OKS in Aimdat Team
"""
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..forms.login_forms import CustomAuthenticationForm
from ..backends import EmailBackend

class ServiceLoginView(LoginView):
    """
    서비스 로그인 뷰
    """
    template_name = 'account/login.html'
    success_url = reverse_lazy('index')
    authentication_form = CustomAuthenticationForm
    backend = EmailBackend

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        
        return super().dispatch(request, *args, **kwargs)