"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.04.01
@author OKS in Aimdat Team
"""
from django.urls import path
from .views.corp_detail_views import CorpDetailView
from .views.faq_views import FaqView
from .views.introduce_views import IntroduceView
from .views.mypage_views import MyPageView
from .views.search_views import SearchView
from .views.terms_views import (
    TermsOfPrivacyView, 
    TermsOfUseView
)


app_name = 'services'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('<int:pk>/', CorpDetailView.as_view(), name="detail"),

    #약관
    path('terms/use/', TermsOfUseView.as_view(), name='terms_of_use'),
    path('terms/privacy/', TermsOfPrivacyView.as_view(), name='terms_of_privacy'),

    #FAQ
    path('faq/', FaqView.as_view(), name='faq'),

    #서비스 소개
    path('introduce/', IntroduceView.as_view(), name='introduce'),

    #마이페이지
    path("mypage/", MyPageView.as_view(), name="mypage")
]