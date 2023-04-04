"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
import secrets

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView,
      PasswordResetDoneView
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

from ..forms.password_reset_forms import (
    CustomPasswordResetForm, 
    CustomSetPasswordForm
)
from ..models import User

class CustomPasswordResetView(UserPassesTestMixin, PasswordResetView):
    """
    서비스 패스워드 초기화 페이지 뷰
    """
    template_name = 'account/password_reset.html'
    email_template_name= 'account/password_reset_email.html'
    form_class = CustomPasswordResetForm

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

            return False
        
        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):                
        return HttpResponseRedirect(reverse_lazy('index'))
    
    def get_success_url(self):
        random_token = secrets.token_hex()
        signer = TimestampSigner()
        self.request.session['reset_token'] = signer.sign(random_token)
        return reverse_lazy('account:password_reset_done')
    
    def form_valid(self, form):
        if not User.objects.filter(email=form.cleaned_data.get('email')).exists():
            form.add_error('email', '존재하지 않는 이메일입니다.')
            return super().form_invalid(form)

        if User.objects.get(email=form.cleaned_data.get('email')).user_classify != 'U':
            form.add_error('email', '소셜 로그인 이용자는 해당 이메일 제공자가 관리하는 페이지에서 비밀번호를 변경하셔야 합니다.')
            return super().form_invalid(form)

        return super().form_valid(form)

class CustomPasswordResetDoneView(UserPassesTestMixin, PasswordResetDoneView):
    """
    서비스 패스워드 초기화 메일 전송 뷰
    """
    template_name = 'account/password_reset_done.html'

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

            return False
        
        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):                
        return HttpResponseRedirect(reverse_lazy('index'))
    
    def get(self, request):
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

class CustomPasswordConfirmView(UserPassesTestMixin, PasswordResetConfirmView):
    """
    서비스 패스워드 재설정 뷰
    """
    template_name = 'account/password_reset_confirm.html'
    form_class = CustomSetPasswordForm

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False
            
            return False
        
        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))

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

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

            return False
        
        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))
    
    def get(self, request):
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