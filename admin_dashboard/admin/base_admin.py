"""
@modified at 2023.03.11
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.models import InquiryAnswer
from admin_dashboard.admin.inquiry_answer_admin import InqueryAnswerAdmin
from admin_dashboard.admin.user_admin import AccountManageAdmin
from django.contrib.admin import AdminSite
from services.models.corp_id import CorpId
from .corp_id_admin import CorpIdAdmin

class CustomAdminSite(AdminSite):
    index_template = 'admin_dashboard/index.html'
    
custom_admin_site = CustomAdminSite(name='custom_admin')

# ModelAdmin 등록
custom_admin_site.register(User, AccountManageAdmin)
custom_admin_site.register(InquiryAnswer, InqueryAnswerAdmin)
custom_admin_site.register(CorpId, CorpIdAdmin)