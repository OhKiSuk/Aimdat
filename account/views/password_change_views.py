"""
@created at 2023.03.05
@author OKS in Aidmat Team

@modified at 2023.03.30
@author OKS in Aimdat Team
"""
import secrets
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import BadHeaderError
from django.shortcuts import redirect
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    """
    비밀번호 변경 뷰
    """
    template_name = 'account/password_change.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('account:login')

        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        random_token = secrets.token_hex()
        signer = TimestampSigner()
        self.request.session['reset_token'] = signer.sign(random_token)
        return reverse_lazy('account:password_change_done')

class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    """
    비밀번호 변경 완료 뷰
    """
    template_name = 'account/password_change_done.html'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
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