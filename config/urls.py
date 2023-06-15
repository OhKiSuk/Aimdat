"""
@modified at 2023.03.11
@author OKS in Aimdat Team

@modified at 2023.03.31
@author OKS in Aimdat Team
"""
from admin_dashboard.admin.base_admin import custom_admin_site
from django.urls import (
    include,
    path
)
from services.views.search_views import SearchView

urlpatterns = [
    path('services/', SearchView.as_view(), name='index'),
    path('admin/', custom_admin_site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('account/', include('account.urls')),
    path('services/', include('services.urls')),
]

handler400 = 'services.views.error_views.custom_400'
handler403 = 'services.views.error_views.custom_403'
handler404 = 'services.views.error_views.custom_404'
handler500 = 'services.views.error_views.custom_500'