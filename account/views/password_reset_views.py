"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.29
@author OKS in Aimdat Team
"""
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..forms.password_reset_forms import CustomPasswordResetForm, CustomSetPasswordForm

class CustomPasswordResetView(PasswordResetView):
    """
    서비스 패스워드 초기화 페이지 뷰
    """
    template_name = 'account/password_reset.html'
    email_template_name= 'account/password_reset_email.html'
    success_url = reverse_lazy('account:password_reset_done')
    form_class = CustomPasswordResetForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    서비스 패스워드 초기화 메일 전송 뷰
    """
    template_name = 'account/password_reset_done.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)

class CustomPasswordConfirmView(PasswordResetConfirmView):
    """
    서비스 패스워드 재설정 뷰
    """
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password_reset_complete')
    form_class = CustomSetPasswordForm

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    패스워드 초기화 완료 후 로그인 뷰
    """
    template_name = 'account/password_reset_complete.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)