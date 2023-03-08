"""
@created at 2023.03.02
@author OKS in Aimdat Team

@modified at 2023.03.07
@author OKS in Aimdat Team
"""
import requests

from config.settings.base import get_secret
from django.contrib.auth import login
from django.http import HttpResponseBadRequest
from django.middleware import csrf
from django.shortcuts import redirect
from django.views.generic import View
from urllib.parse import urlencode

from account.models import User

class GoogleLoginView(View):
    """
    구글 로그인 뷰
    """
    def get(self, request):
        #CSRF 방지
        request.session['state'] = csrf.get_token(request)

        url = 'https://accounts.google.com/o/oauth2/v2/auth'
        params = {
            'response_type': 'code',
            'client_id': get_secret("google_client_id"),
            'redirect_uri': 'http://127.0.0.1:8000/account/google/login/callback/',
            'scope': 'https://www.googleapis.com/auth/userinfo.email',
            'state': request.session['state']
        }

        return redirect(f'{url}?{urlencode(params)}')
    
class GoogleCallbackView(View):
    def get(self, request):
        if request.GET.get('state') != request.session.get('state'):
            return HttpResponseBadRequest()
        
        if request.GET.get('code') == None:
            return HttpResponseBadRequest()
        
        #액세스 토큰 획득
        url = 'https://oauth2.googleapis.com/token'
        params = {
            'client_id': get_secret("google_client_id"),
            'client_secret': get_secret("google_client_secret"),
            'code': request.GET.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://127.0.0.1:8000/account/google/login/callback/'
        }

        response = requests.post(url, params=params)
        response_to_json = response.json()
        self.access_token = response_to_json.get('access_token')

        get_email = self.get_google_email()
        email = get_email.get('email')

        #회원가입 여부 확인
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
        else:
            user = User.objects.create_user(email=email, password='')
            user.user_classify = 'G'
            user.terms_of_use_agree = True
            user.terms_of_privacy_agree = True
            user.set_unusable_password()
            user.save()

        login(request, user, backend='account.backends.EmailBackend')
        return redirect("account:signup")
    
    def get_google_email(self):
        """
        구글 이메일을 가져오는 함수
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        response = requests.get(url, headers=headers)

        return response.json()