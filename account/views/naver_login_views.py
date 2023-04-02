"""
@created at 2023.03.02
@author OKS in Aimdat Team

@modified at 2023.04.02
@author OKS in Aimdat Team
"""
import requests
import json

from config.settings.base import get_secret
from django.contrib.auth import (
    login,
    logout
)
from django.http import (
    HttpResponseBadRequest,
    HttpResponseServerError
)
from django.middleware import csrf
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import View

from ..models import User

class NaverLoginView(View):
    """
    네이버 로그인 뷰
    """
    def get(self, request):
        #네이버 인증(로그인) 절차
        url = 'https://nid.naver.com/oauth2.0/authorize'
        request.session['state'] = csrf.get_token(request)
        response_type = 'code'
        client_id =  get_secret("naver_client_id")
        redirect_uri = 'http://127.0.0.1:8000/account/naver/login/callback/'
        state = request.session['state']
        login_url = f"{url}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&state={state}"

        return redirect(login_url)
    
class NaverCallbackView(View):
    """
    네이버 로그인 후 콜백
    """
    def get(self, request):
        if request.GET.get('state') != request.session.get('state'):
            return HttpResponseBadRequest()
        
        if request.GET.get('code') == None:
            return HttpResponseBadRequest()

        #토큰 값 생성
        url = 'https://nid.naver.com/oauth2.0/token'
        params = {
            'grant_type': 'authorization_code',
            'client_id': get_secret("naver_client_id"),
            'client_secret': get_secret("naver_client_secret"),
            'code': request.GET.get('code'),
            'state': request.session.get('state')
        }
        response = requests.post(url, params=params)
        token_to_json = json.loads(response.text)
        self.access_token = token_to_json.get('access_token')

        #네이버 계정 프로필 가져오기
        profile = self.get_naver_profile()
        # **네이버 이메일 정보는 연락처 이메일임**
        email = profile.get('response', {}).get('email')

        #회원가입 여부 확인
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
        else:
            user = User.objects.create_user(email=email, password='')
            user.user_classify = "N"
            user.terms_of_use_agree = True
            user.terms_of_privacy_agree = True
            user.is_not_teen = True
            user.refresh_token = token_to_json.get('refresh_token')
            user.set_unusable_password()
            user.save()

        login(request, user, backend='account.backends.EmailBackend')
        return redirect('index')
    
    def get_naver_profile(self):
        """
        네이버 프로필 값을 가져오는 함수
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        url = 'https://openapi.naver.com/v1/nid/me'
        response = requests.get(url, headers=headers)

        return response.json()
    
class NaverLinkOffView(View):
    """
    네이버 연동 해제 뷰(회원 탈퇴)
    """
    def get(self, request):
        #토큰 재발급
        url = 'https://nid.naver.com/oauth2.0/token'
        params = {
            'grant_type': 'refresh_token',
            'client_id': get_secret("naver_client_id"),
            'client_secret': get_secret("naver_client_secret"),
            'refresh_token': request.user.refresh_token
        }
        response = requests.post(url, params=params)
        token_to_json = json.loads(response.text)
        self.access_token = token_to_json.get('access_token')

        #네이버 연동 해제
        linkoff = self.__linkoff()
        if linkoff != 'success':
            return HttpResponseServerError()
        else:
            #로그아웃
            email = request.user.email
            logout(request)
            User.objects.get(email=email).delete()

            #세션 제거
            self.request.session.flush()
            return redirect(reverse_lazy('account:login'))

    def __linkoff(self):
        """
        네이버 연동 해제
        """
        url = 'https://nid.naver.com/oauth2.0/token'
        params = {
            'grant_type': 'delete',
            'client_id': get_secret("naver_client_id"),
            'client_secret': get_secret("naver_client_secret"),
            'access_token': self.access_token,
            'service_provider': 'NAVER'
        }
        response = requests.post(url, params=params)
        response_to_json = json.loads(response.text)

        return response_to_json.get('result')