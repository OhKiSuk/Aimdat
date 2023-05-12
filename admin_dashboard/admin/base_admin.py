"""
@modified at 2023.05.01
@author OKS in Aimdat Team
"""
from account.forms.login_forms import CustomAuthenticationForm
from account.models import User
from admin_dashboard.admin.user_admin import AccountManageAdmin
from axes.models import (
    AccessFailureLog, 
    AccessLog, 
    AccessAttempt
)
from datetime import (
    datetime, 
    timedelta
)
from django.contrib.admin import AdminSite
from django.db.models import Count
from django.db.models.functions import (
    TruncMonth, 
    TruncYear, 
    TruncDay
)
from django.urls import path
from services.models.inquiry import Inquiry

from .axes_admin import (
    AccessAttemptAdmin, 
    AccessFailureAdmin, 
    AccessSuccessAdmin
)
from ..views.collect_data_views import (
    CollectCorpInfoView, 
    CollectStockPriceView, 
    CollectFcorpFinancialStatementsView,
    CollectDcorpFinancialStatementsView,
    CollectInvestmentIndexView
)
from ..views.corp_manage_views import (
    ManageCorpIdListView, 
    ManageCorpIdUpdateView,
    ManageCorpInfoListView,
    ManageCorpInfoUpdateView,
    ManageCorpFinancialStatementsAddView,
    ManageCorpFinancialStatementsDeleteView,
    ManageCorpFinancialStatementsSearchView,
    ManageCorpFinancialStatementsUpdateView,
)
from ..views.inquiry_manage_views import (
    InquiryListView, 
    InquiryAddAnswerView
)

class CustomAdminSite(AdminSite):
    index_template = 'admin_dashboard/index.html'
    login_template = 'admin_dashboard/admin_login.html'
    login_form = CustomAuthenticationForm

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # 재무제표 수집
            path('collect/fs/fcorp/', custom_admin_site.admin_view(CollectFcorpFinancialStatementsView.as_view()), name='collect_fs_fcorp'),
            path('collect/fs/dcorp/', custom_admin_site.admin_view(CollectDcorpFinancialStatementsView.as_view()), name='collect_fs_dcorp'),

            # 주가정보 수집
            path('collect/stock/', custom_admin_site.admin_view(CollectStockPriceView.as_view()), name='collect_stock'),

            # 기업정보 수집
            path('collect/corp/info/', custom_admin_site.admin_view(CollectCorpInfoView.as_view()), name='collect_corp_info'),

            # 투자지표 수집 및 저장
            path('collect/corp/investment/index/', custom_admin_site.admin_view(CollectInvestmentIndexView.as_view()), name='collect_corp_invsetment_index'),
            
            # 기업 식별 목록 관리
            path('manage/corp/id/list/', custom_admin_site.admin_view(ManageCorpIdListView.as_view()), name='manage_corp_id_list'),
            path('manage/corp/id/update/<int:pk>/', custom_admin_site.admin_view(ManageCorpIdUpdateView.as_view()), name='manage_corp_id_update'),

            # 기업 정보 관리
            path('manage/corp/info/list/', custom_admin_site.admin_view(ManageCorpInfoListView.as_view()), name='manage_corp_info_list'),
            path('manage/corp/info/update/<int:pk>/', custom_admin_site.admin_view(ManageCorpInfoUpdateView.as_view()), name='manage_corp_info_update'),

            # 기업 재무제표 관리
            path('manage/corp/fs/add/', custom_admin_site.admin_view(ManageCorpFinancialStatementsAddView.as_view()), name='manage_corp_fs_add'),
            path('manage/corp/fs/delete/', custom_admin_site.admin_view(ManageCorpFinancialStatementsDeleteView.as_view()), name='manage_corp_fs_delete'),
            path('manage/corp/fs/search/', custom_admin_site.admin_view(ManageCorpFinancialStatementsSearchView.as_view()), name='manage_corp_fs_search'),
            path('manage/corp/fs/update/', custom_admin_site.admin_view(ManageCorpFinancialStatementsUpdateView.as_view()), name='manage_corp_fs_update'),

            #문의사항 관리
            path('inquiry/manage/', custom_admin_site.admin_view(InquiryListView.as_view()), name='inquiry_manage'),
            path('inquiry/manage/add/answer/<int:pk>', custom_admin_site.admin_view(InquiryAddAnswerView.as_view()), name='add_inquiry_answer')
        ]

        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        signup_period = request.GET.get('period', 'week')

        #1:1 문의 최근 목록
        if Inquiry.objects.all().exists():
            extra_context['inquiry'] = Inquiry.objects.all().values('created_at', 'title').order_by('-created_at')[:5]

        #총 가입자 수
        if User.objects.filter(is_admin=False).exists():
            extra_context['total_user'] = User.objects.filter(is_admin=False).count()

            if signup_period == 'month':
                #월별 가입자 현황
                now = datetime.now()
                queryset = User.objects.annotate(
                    month=TruncMonth('created_at')
                ).values('month').annotate(
                    count=Count('id')
                ).filter(month__lte=now, is_admin=False).order_by('-month')[:12]

                extra_context['user_count_label'] = [obj['month'].strftime('%Y-%m') for obj in queryset]
                extra_context['user_count_data'] = [obj['count'] for obj in queryset]
            elif signup_period == 'year':
                #연도별 가입자 현황
                now = datetime.now()
                queryset = User.objects.annotate(
                    year=TruncYear('created_at')
                ).values('year').annotate(
                    count=Count('id')
                ).filter(year__lte=now, is_admin=False).order_by('-year')[:12]

                extra_context['user_count_label'] = [obj['year'].strftime('%Y') for obj in queryset]
                extra_context['user_count_data'] = [obj['count'] for obj in queryset]
            else: 
                #일주일 간 가입자 현황
                now = datetime.now()
                week_ago = now - timedelta(days=6)

                dates = [week_ago + timedelta(days=i) for i in range(7)]

                queryset = User.objects.annotate(
                    day=TruncDay('created_at')
                ).values('day').annotate(
                    count=Count('id')
                ).filter(day__gte=week_ago, day__lte=now, is_admin=False).order_by('day')

                counts = {obj['day'].date(): obj['count'] for obj in queryset}

                data = [counts.get(date.date(), 0) for date in dates]

                extra_context['user_count_label'] = [date.strftime('%Y-%m-%d') for date in dates]
                extra_context['user_count_data'] = data

        return super().index(request, extra_context)
    
custom_admin_site = CustomAdminSite(name='custom_admin')

# ModelAdmin 등록
custom_admin_site.register(User, AccountManageAdmin)
custom_admin_site.register(AccessAttempt, AccessAttemptAdmin)
custom_admin_site.register(AccessFailureLog, AccessFailureAdmin)
custom_admin_site.register(AccessLog, AccessSuccessAdmin)