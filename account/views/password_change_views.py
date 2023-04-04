"""
@created at 2023.03.05
@author OKS in Aidmat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
import secrets

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordChangeView, 
    PasswordChangeDoneView
)
from django.core.signing import (
    BadSignature, 
    SignatureExpired, 
    TimestampSigner
)
from django.http import (
    BadHeaderError,
    HttpResponseRedirect
)
from django.urls import reverse_lazy

from ..forms.password_change_forms import CustomPasswordChangeForm

class CustomPasswordChangeView(UserPassesTestMixin, PasswordChangeView):
    """
    비밀번호 변경 뷰
    """
    template_name = 'account/password_change.html'
    form_class = CustomPasswordChangeForm

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))
    
    def get_success_url(self):
        random_token = secrets.token_hex()
        signer = TimestampSigner()
        self.request.session['reset_token'] = signer.sign(random_token)
        return reverse_lazy('account:password_change_done')

class CustomPasswordChangeDoneView(UserPassesTestMixin, PasswordChangeDoneView):
    """
    비밀번호 변경 완료 뷰
    """
    template_name = 'account/password_change_done.html'

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))
    
    def get(self, request, *args, **kwargs):
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
        return super().get(request)