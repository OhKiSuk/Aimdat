"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.04.03
@author OKS in Aimdat Team

@modified at 2023.04.07
@author JSU in Aimdat Team

@modified at 2023.04.09
@author JSU in Aimdat Team
"""
from django.urls import path

from .views.analysis_views import AnalysisView
from .views.corp_detail_views import CorpDetailView
from .views.faq_views import FaqView
from .views.inquiry_views import AddInquiryView, InquiryDetailView, InquiryView
from .views.introduce_views import IntroduceView
from .views.mypage_views import MyPageView
from .views.search_views import SearchView
from .views.terms_views import TermsOfPrivacyView, TermsOfUseView

app_name = 'services'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('<int:id>/', CorpDetailView.as_view(), name="detail"),
    path('analysis/', AnalysisView.as_view(), name='analysis'),

    #약관
    path('terms/use/', TermsOfUseView.as_view(), name='terms_of_use'),
    path('terms/privacy/', TermsOfPrivacyView.as_view(), name='terms_of_privacy'),

    #FAQ
    path('faq/', FaqView.as_view(), name='faq'),

    #서비스 소개
    path('introduce/', IntroduceView.as_view(), name='introduce'),

    #마이페이지
    path("mypage/", MyPageView.as_view(), name="mypage"),

    #1:1 문의
    path('mypage/inquiry', InquiryView.as_view(), name='inquiry'),
    path('mypage/inquiry/<int:id>', InquiryDetailView.as_view(), name='inquiry_detail'),
    path('mypage/inquiry/add/', AddInquiryView.as_view(), name='add_inquiry')
]