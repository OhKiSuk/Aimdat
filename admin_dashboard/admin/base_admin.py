"""
@modified at 2023.03.11
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.admin.user_admin import AccountManageAdmin
from django.contrib.admin import AdminSite

class CustomAdminSite(AdminSite):
    index_template = 'admin_dashboard/index.html'
    
custom_admin_site = CustomAdminSite(name='custom_admin')

# ModelAdmin 등록
custom_admin_site.register(User, AccountManageAdmin)