"""
@created at 2023.03.22
@author JSU in Aimdat Team

@modified at 2023.05.31
@author OKS in Aimdat Team
"""
import requests

from datetime import (
    datetime, 
    timedelta
)
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView
from config.settings.base import get_secret

from ..models.corp_id import CorpId
from ..models.corp_info import CorpInfo
from ..models.investment_index import InvestmentIndex
from ..models.stock_price import StockPrice

class CorpInquiryView(UserPassesTestMixin, DetailView):
    model = CorpId
    template_name = 'services/corp_inquiry.html'
    context_object_name = 'corp_id'
    pk_url_kwarg = 'id'
    
    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False
            if self.request.user.expiration_date.date() >= timezone.now().date():
                return True
            
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs.get(self.pk_url_kwarg)
        stock_price_obj = StockPrice.objects.filter(Q(corp_id__exact = id)).order_by('trade_date')
        disclosure_data = self.disclosure_data(id)
        
        fs_type_name = self.request.GET.get('fs_type', 'cfs')
        
        # 윤년 계산
        if (datetime.now().year % 4 == 0 and datetime.now().year % 100 != 0) or datetime.now().year % 400 == 0:
            week_52 = (datetime.now() - timedelta(days=366)).strftime('%Y-%m-%d')
        else:
            week_52 = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 공시정보
        context['page_obj'] = self.paging_disclosure_data(disclosure_data)

        context['corp_info'] = CorpInfo.objects.get(Q(corp_id__exact = id))
        context['latest_stock_info'] = stock_price_obj.latest('trade_date')
        context['stock_data'] = stock_price_obj
        context['week_52_price'] = stock_price_obj.get(Q(trade_date__exact = str(week_52))) if stock_price_obj.filter(Q(trade_date__exact = str(week_52))).exists() else None
        context['report_data'] = self.recent_report(id, fs_type_name)
        
        return context

    def recent_report(self, id, fs_type_name):
        """
        최근 3년, 4분기 데이터 전체 조회
        """
        # 별도, 연결 구분
        if fs_type_name == 'sfs':
            fs_type = 5
        else:
            fs_type = 0

        exclude_fields = ['id', 'corp_id', 'fs_type']  # 제외할 필드 목록
        fields = [f.name for f in InvestmentIndex._meta.fields if f.name not in exclude_fields]

        data = InvestmentIndex.objects.filter(corp_id=id, fs_type=fs_type).order_by('year', 'quarter').values(*fields)

        return data

    # 공시 데이터 API 요청
    def disclosure_data(self, id):
        stock_code = CorpId.objects.get(id=id).stock_code
        bgn_de = (datetime.today()-timedelta(days=365 * 3)).strftime('%Y%m%d'), # 오늘로부터 최대 3년 전까지의 데이터 조회(최대 100개)

        url = 'https://opendart.fss.or.kr/api/list.json'
        params = {
            'crtfc_key': get_secret('crtfc_key'), 
            'corp_code': stock_code, 
            'bgn_de': bgn_de,
            'page_count': 100
        }

        response = requests.get(url, params=params)
        response_to_json = response.json()

        if response_to_json['status'] == '000':
            return response_to_json['list']

    # 공시 데이터 페이징
    def paging_disclosure_data(self, data):
        paginator = Paginator(data, 20)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        return page_obj