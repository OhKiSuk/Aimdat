"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.03.28
@author OKS in Aimdat Team
"""
import random
from account.forms.signup_forms import SendPinForm
from account.forms.signup_forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

class SignUpView(FormView):
    template_name = 'account/signup.html'
    form_class = UserCreationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')
        else:
            return super().dispatch(request, *args, **kwargs)

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

class SendPinView(FormView):
    form_class = SendPinForm
    success_url = reverse_lazy('account:signup')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            raise PermissionDenied()
        else:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        회원가입 정보 입력 시 PIN 번호 생성 후 이메일 전송
        """
        pin = '{:06d}'.format(random.randint(100_000, 999_999))
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