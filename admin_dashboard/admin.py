"""
@modified at 2023.03.09
@author OKS in Aimdat Team
"""
from django.contrib.admin import AdminSite

from account.models import User

class CustomAdminSite(AdminSite):
    index_template = 'admin_dashboard/index.html'
    
custom_admin_site = CustomAdminSite(name='custom_admin')
custom_admin_site.register(User)