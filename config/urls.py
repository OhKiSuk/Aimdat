"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
@modified at 2023.03.09
@author OKS in Aimdat Team
"""
from admin_dashboard.admin import custom_admin_site
from django.urls import path, include

from account.views.login_views import ServiceLoginView

urlpatterns = [
    path('', ServiceLoginView.as_view(), name='index'),
    path('admin/', custom_admin_site.urls),
    path('account/', include('account.urls')),
]