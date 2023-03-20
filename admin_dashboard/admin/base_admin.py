"""
@modified at 2023.03.11
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.models import InquiryAnswer
from admin_dashboard.admin.inquiry_answer_admin import InqueryAnswerAdmin
from admin_dashboard.admin.user_admin import AccountManageAdmin
from django.contrib.admin import AdminSite
from django.urls import path
from ..views.corp_manage_views import CorpManageView, CorpIdChangeView, CorpInfoChangeView, CorpSummaryFinancialStatementsChangeView
from ..views.marketing_views import MarketingView

class CustomAdminSite(AdminSite):
    index_template = 'admin_dashboard/index.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('marketing/statistics', custom_admin_site.admin_view(MarketingView.as_view()) , name='marketing'),
            path('corp/manage', custom_admin_site.admin_view(CorpManageView.as_view()), name='corp_manage'),
            path('corp/manage/id/<int:pk>/', custom_admin_site.admin_view(CorpIdChangeView.as_view()), name='corp_id_change'),
            path('corp/manage/info/<int:pk>/', custom_admin_site.admin_view(CorpInfoChangeView.as_view()), name='corp_info_change'),
            path('corp/manage/summary/<int:pk>/', custom_admin_site.admin_view(CorpSummaryFinancialStatementsChangeView.as_view()), name='corp_summary_change'),
        ]

        return custom_urls + urls
    
custom_admin_site = CustomAdminSite(name='custom_admin')

# ModelAdmin 등록
custom_admin_site.register(User, AccountManageAdmin)
custom_admin_site.register(InquiryAnswer, InqueryAnswerAdmin)