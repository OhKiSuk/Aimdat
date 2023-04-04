"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
import random

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from ..forms.signup_forms import (
    SendPinForm,
    UserCreationForm
)
class SignUpView(UserPassesTestMixin, FormView):
    template_name = 'account/signup.html'
    form_class = UserCreationForm

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return not self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))

    def form_valid(self, form):
        """
        PIN 번호를 통한 이메일 검증
        """
        session_pin = self.request.session.get('pin')
        pin = form.cleaned_data.get('pin')

        if session_pin and pin and session_pin == pin:
            form.save()
            return redirect('index')

        del self.request.session['pin']
        return super().form_valid(form)

class SendPinView(UserPassesTestMixin, FormView):
    form_class = SendPinForm
    success_url = reverse_lazy('account:signup')

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return not self.request.user.is_authenticated

    def form_valid(self, form):
        """
        회원가입 정보 입력 시 PIN 번호 생성 후 이메일 전송
        """
        pin = '{:06d}'.format(random.randint(0, 999_999))
        email = self.request.POST.get('email')
        self.request.session['pin'] = pin

        send_mail(
            '[Aimdat] 회원가입 PIN 번호 발송 안내',
            '회원가입 시 입력하셔야 할 PIN 번호는 {} 입니다.'.format(pin),
            'no-reply@aimdat.com',
            [email],
            fail_silently=False
        )
        self.request.session.set_expiry(1800)
        
        return super().form_valid(form)