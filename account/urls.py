"""
@created at 2023.02.27
@author OKS in Aimdat Team

@modified at 2023.03.07
@author OKS in Aimdat Team
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from .views.signup_views import SignUpView, SendPinView
from .views.login_views import ServiceLoginView
from .views.kakao_login_views import KakaoLoginView, KakaoCallbackView
from .views.naver_login_views import NaverLoginView, NaverCallbackView
from .views.google_login_views import GoogleLoginView, GoogleCallbackView
from .views.password_reset_views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordConfirmView, CustomPasswordResetCompleteView
from .views.password_change_views import CustomPasswordChangeView, CustomPasswordChangeDoneView

app_name = 'account'

urlpatterns = [
    # 로그인
    path('login/', ServiceLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('google/login', GoogleLoginView.as_view(), name='google_login'),
    path('google/login/callback/', GoogleCallbackView.as_view(), name='google_login_callback'),
    path('naver/login', NaverLoginView.as_view(), name='naver_login'),
    path('naver/login/callback/', NaverCallbackView.as_view(), name='naver_login_callback'),
    path('kakao/login', KakaoLoginView.as_view(), name='kakao_login'),
    path('kakao/login/callback/', KakaoCallbackView.as_view(), name='kakao_login_callback'),

    #회원가입
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signup/send/', SendPinView.as_view(), name='send_pin'),

    #비밀번호 재설정
    path('password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', CustomPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    #비밀번호 변경
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
]