"""
@created at 2023.03.15
@author JSU in Aimdat Team
"""
from django.urls import path
from .views.search_views import SearchView

app_name = 'services'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
]
