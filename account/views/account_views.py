"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.03.07
@author OKS in Aimdat Team
"""
import random

from account.forms.account_forms import SendPinForm
from account.forms.signup_forms import UserCreationForm
from django.core.mail import send_mail, BadHeaderError
from django.urls import reverse_lazy
from django.views.generic import FormView

class SignUpView(FormView):
    template_name = 'account/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('account:signup')

    def form_valid(self, form):
        """
        PIN 번호를 통한 이메일 검증
        """
        session_pin = self.request.session.get('pin')
        pin = form.cleaned_data.get('pin')

        if session_pin and pin and session_pin == pin:
            form.save()
        else:
            return super().form_invalid(form)

        del self.request.session['pin']
        return super().form_valid(form)

class SendPinView(FormView):
    form_class = SendPinForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        """
        회원가입 정보 입력 시 PIN 번호 생성 후 이메일 전송
        """
        pin = str(random.randint(100_000, 999_999))
        email = self.request.POST.get('email')
        self.request.session['pin'] = pin

        try:
            send_mail(
                '[Aimdat] 회원가입 PIN 번호 발송 안내',
                '회원가입 시 입력하셔야 할 PIN 번호는 {} 입니다.'.format(pin),
                'no-reply@aimdat.com',
                [email],
                fail_silently=False
            )
            self.request.session.set_expiry(1800)
        except BadHeaderError:
            return super().form_invalid(form)
        
        return super().form_valid(form)