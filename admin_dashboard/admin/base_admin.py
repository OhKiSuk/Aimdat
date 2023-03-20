"""
@modified at 2023.03.20
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.admin.user_admin import AccountManageAdmin
from django.contrib.admin import AdminSite
from django.urls import path
from ..views.corp_manage_views import CorpManageView, CorpIdChangeView, CorpInfoChangeView, CorpSummaryFinancialStatementsChangeView
from ..views.marketing_views import MarketingView
from ..views.inquiry_manage_views import InquiryListView, InquiryAddAnswerView

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

            #문의사항 관리
            path('inquiry/manage', custom_admin_site.admin_view(InquiryListView.as_view()), name='inquiry_manage'),
            path('inquiry/manage/add/answer/<int:pk>', custom_admin_site.admin_view(InquiryAddAnswerView.as_view()), name='add_inquiry_answer')
        ]

        return custom_urls + urls
    
custom_admin_site = CustomAdminSite(name='custom_admin')

# ModelAdmin 등록
custom_admin_site.register(User, AccountManageAdmin)