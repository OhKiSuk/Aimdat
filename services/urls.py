"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.06.16
@author OKS in Aimdat Team
"""
from django.urls import path

from .views.analysis_views import AnalysisView
from .views.corp_inquiry_views import CorpInquiryView
from .views.faq_views import FaqView
from .views.mypage_views import MyPageView
from .views.search_views import SearchView
from .views.terms_views import (
    TermsOfPrivacyView, 
    TermsOfUseView
    )

app_name = 'services'

urlpatterns = [
    # 검색
    path('search', SearchView.as_view(), name='search'),
    
    # 기업 조회
    path('corp/inquiry/<int:id>', CorpInquiryView.as_view(), name="corp_inquiry"),

    # 기업 비교/분석
    path('analysis/', AnalysisView.as_view(), name='analysis'),

    #약관
    path('terms/use/', TermsOfUseView.as_view(), name='terms_of_use'),
    path('terms/privacy/', TermsOfPrivacyView.as_view(), name='terms_of_privacy'),

    #FAQ
    path('faq/', FaqView.as_view(), name='faq'),

    #마이페이지
    path("mypage/", MyPageView.as_view(), name="mypage"),
]