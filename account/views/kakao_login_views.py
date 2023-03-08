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

from account.models import User

class KakaoLoginView(View):
    """
    카카오 로그인 뷰
    """
    def get(self, request):
        #CSRF 방지를 위한 token 생성
        request.session['state'] = csrf.get_token(request)

        #카카오 로그인 절차
        url = 'https://kauth.kakao.com/oauth/authorize'
        client_id =  get_secret("kakao_rest_api_key")
        redirect_uri = 'http://127.0.0.1:8000/account/kakao/login/callback/'
        response_type = 'code'
        state = request.session['state']
        scope = 'account_email'
        login_url = f"{url}?&client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&state={state}&scope={scope}"

        return redirect(login_url)
    
class KakaoCallbackView(View):
    """
    카카오 로그인 후 콜백
    """
    def get(self, request):
        if request.GET.get('state') != request.session.get('state'):
            return HttpResponseBadRequest()

        if request.GET.get('code') == None:
            return HttpResponseBadRequest()

        #토큰 값 생성
        url = 'https://kauth.kakao.com/oauth/token'
        params = {
            'grant_type': 'authorization_code',
            'client_id': get_secret("kakao_rest_api_key"),
            'redirect_uri': 'http://127.0.0.1:8000/account/kakao/login/callback/',
            'code': request.GET.get('code'),
            'client_secret': get_secret("kakao_client_secret"),
        }
        response = requests.post(url, params=params)
        response_to_json = response.json()
        self.access_token = response_to_json.get('access_token')

        #프로필 가져오기
        profile = self.get_kakao_profile()
        email = profile.get('kakao_account', {}).get('email')

        #회원가입 여부 확인
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
        else:
            user = User.objects.create_user(email=email, password='')
            user.user_classify = "K"
            user.terms_of_use_agree = True
            user.terms_of_privacy_agree = True
            user.set_unusable_password()
            user.save()

        login(request, user, backend='account.backends.EmailBackend')
        return redirect('account:signup')
    
    def get_kakao_profile(self):
        """
        카카오 프로필 값을 가져오는 함수
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        url = 'https://kapi.kakao.com/v2/user/me'
        response = requests.get(url, headers=headers)

        return response.json()