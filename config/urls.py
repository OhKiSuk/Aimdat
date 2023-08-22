"""
@modified at 2023.03.11
@author OKS in Aimdat Team

@modified at 2023.08.11
@author OKS in Aimdat Team
"""
from admin_dashboard.admin.base_admin import custom_admin_site
from django.contrib.sitemaps.views import sitemap
from django.urls import (
    include,
    path
)
from services.views.home_views import HomeView
from .sitemaps import StaticSitemap, CorpInquriySitemap

sitemaps = {
    "services": StaticSitemap(app_name='services'),
    "corp_inquiry": CorpInquriySitemap
}

urlpatterns = [
    path('', HomeView.as_view(), name='index'),
    path('admin/', custom_admin_site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('account/', include('account.urls')),
    path('services/', include('services.urls')),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap")
    
]

handler400 = 'services.views.error_views.custom_400'
handler403 = 'services.views.error_views.custom_403'
handler404 = 'services.views.error_views.custom_404'
handler500 = 'services.views.error_views.custom_500'