"""
@modified at 2023.03.21
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.admin.user_admin import AccountManageAdmin
from axes.models import AccessFailureLog, AccessLog, AccessAttempt
from datetime import datetime, timedelta
from django.contrib.admin import AdminSite
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncYear, TruncDay
from django.urls import path
from services.models.inquiry import Inquiry
from .axes_admin import AccessAttemptAdmin, AccessFailureAdmin, AccessSuccessAdmin
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