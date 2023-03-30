"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.03.30
@author OKS in Aimdat Team
"""
from django.urls import path
from .views.search_views import SearchView
from .views.corp_detail_views import CorpDetailView
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
]
