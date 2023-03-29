"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.29
@author OKS in Aimdat Team
"""
import secrets
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.http import BadHeaderError
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..forms.password_reset_forms import CustomPasswordResetForm, CustomSetPasswordForm

class CustomPasswordResetView(PasswordResetView):
    """
    서비스 패스워드 초기화 페이지 뷰
    """
    template_name = 'account/password_reset.html'
    email_template_name= 'account/password_reset_email.html'
    form_class = CustomPasswordResetForm

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        random_token = secrets.token_hex()
        signer = TimestampSigner()
        self.request.session['reset_token'] = signer.sign(random_token)
        return reverse_lazy('account:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """
    서비스 패스워드 초기화 메일 전송 뷰
    """
    template_name = 'account/password_reset_done.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')
        
        reset_token = self.request.session.get('reset_token')
        if not reset_token:
            raise BadHeaderError('잘못된 접근입니다.')
        
        try:
            signer = TimestampSigner()
            signer.unsign(reset_token, max_age=300)
        except SignatureExpired:
            raise BadHeaderError('잘못된 접근입니다.')
        except BadSignature:
            raise BadHeaderError('잘못된 접근입니다.')

        del self.request.session['reset_token']
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordConfirmView(PasswordResetConfirmView):
    """
    서비스 패스워드 재설정 뷰
    """
    template_name = 'account/password_reset_confirm.html'
    form_class = CustomSetPasswordForm

    def get_success_url(self):
        random_token = secrets.token_hex()
        signer = TimestampSigner()
        self.request.session['reset_token'] = signer.sign(random_token)

        return reverse_lazy('account:password_reset_complete')
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """
    패스워드 초기화 완료 후 로그인 뷰
    """
    template_name = 'account/password_reset_complete.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('account:login')
        
        reset_token = self.request.session.get('reset_token')
        if not reset_token:
            raise BadHeaderError('잘못된 접근입니다.')
        
        try:
            signer = TimestampSigner()
            signer.unsign(reset_token, max_age=300)
        except SignatureExpired:
            raise BadHeaderError('잘못된 접근입니다.')
        except BadSignature:
            raise BadHeaderError('잘못된 접근입니다.')

        del self.request.session['reset_token']
        return super().dispatch(request, *args, **kwargs)