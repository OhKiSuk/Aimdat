"""
@created at 2023.03.15
@author JSU in Aimdat Team
"""
from django.urls import path
from .views.search_views import SearchView
from .views.corp_detail_views import CorpDetailView

app_name = 'services'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('<int:pk>/', CorpDetailView.as_view(), name="detail"),
]
