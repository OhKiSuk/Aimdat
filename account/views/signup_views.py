"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.04.05
@author OKS in Aimdat Team
"""
import random

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest
)
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import FormView

from ..forms.signup_forms import UserCreationForm

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
    
    def post(self, request):
        """
        PIN 번호 전송
        """

        #Ajax 요청 시에만 PIN 번호 전송
        if request.headers.get('x-requested-with') is not None:

            if request.POST.get('email') is None:
                return HttpResponseBadRequest()
            
            pin = '{:06d}'.format(random.randint(0, 999_999))
            email = self.request.POST.get('email')
            self.request.session['pin'] = pin

            #이메일 템플릿
            email_template = 'account/signup_email.html'
            email_context = {
                'pin': pin
            }
            html_message = render_to_string(email_template, email_context)

            send_mail(
                '[Aimdat] 회원가입 PIN 번호 발송 안내',
                '',
                'no-reply@aimdat.com',
                [email],
                fail_silently=False,
                html_message=html_message
            )
            self.request.session.set_expiry(1800)

        return super().post(request)

    def form_valid(self, form):
        """
        PIN 번호를 통한 이메일 검증 후 회원가입 처리
        """
        session_pin = self.request.session.get('pin')
        pin = form.cleaned_data.get('pin')

        if session_pin and pin and session_pin == pin:
            form.save()
            messages.success(self.request, '회원 가입이 완료되었습니다.')
            return redirect('account:login')

        del self.request.session['pin']
        return super().form_valid(form)