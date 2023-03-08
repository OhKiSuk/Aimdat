"""
@created at 2023.03.05
@author OKS in Aidmat Team
"""
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.shortcuts import redirect
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    """
    비밀번호 변경 뷰
    """
    template_name = 'account/password_change.html'
    success_url = reverse_lazy('account:password_change_done')

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """
    비밀번호 변경 완료 뷰
    """
    template_name = 'account/password_change_done.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)