"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.04.05
@author OKS in Aimdat Team
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from .views.delete_account_views import DeleteAccountView
from .views.google_login_views import (
    GoogleLoginView, 
    GoogleCallbackView,
    GoogleLinkOffView
)
"""
from .views.kakao_login_views import (
    KakaoLoginView, 
    KakaoCallbackView,
    KakaoLinkOffView
)
"""
from .views.login_views import ServiceLoginView
from .views.naver_login_views import (
    NaverLoginView, 
    NaverCallbackView,
    NaverLinkOffView
)
from .views.password_reset_views import (
    CustomPasswordResetView, 
    CustomPasswordResetDoneView, 
    CustomPasswordConfirmView, 
    CustomPasswordResetCompleteView
)
from .views.password_change_views import (
    CustomPasswordChangeView, 
    CustomPasswordChangeDoneView
)
from .views.signup_views import SignUpView

app_name = 'account'

urlpatterns = [
    # 로그인
    path('login/', ServiceLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='account:login'), name='logout'),
    path('google/login', GoogleLoginView.as_view(), name='google_login'),
    path('google/login/callback/', GoogleCallbackView.as_view(), name='google_login_callback'),
    path('naver/login', NaverLoginView.as_view(), name='naver_login'),
    path('naver/login/callback/', NaverCallbackView.as_view(), name='naver_login_callback'),
    #path('kakao/login', KakaoLoginView.as_view(), name='kakao_login'),
    #path('kakao/login/callback/', KakaoCallbackView.as_view(), name='kakao_login_callback'),

    #소셜계정 연동 해제
    path("naver/login/linkoff", NaverLinkOffView.as_view(), name="naver_login_linkoff"),
    #path("kakao/login/linkoff", KakaoLinkOffView.as_view(), name="kakao_login_linkoff"),
    path("google/login/linkoff", GoogleLinkOffView.as_view(), name="google_login_linkoff"),

    #회원가입
    path('signup/', SignUpView.as_view(), name='signup'),

    #비밀번호 재설정
    path('password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', CustomPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    #비밀번호 변경
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),

    #계정 탈퇴
    path('delete/', DeleteAccountView.as_view(), name='delete_account'),
]