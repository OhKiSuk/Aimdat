"""
@created at 2023.03.22
@author JSU in Aimdat Team

@modified at 2023.05.12
@author JSU in Aimdat Team
"""

import json
from datetime import datetime, timedelta

import requests
from django.apps import apps
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


class CorpDetailView(UserPassesTestMixin, DetailView):
    model = CorpId
    template_name = 'services/corp_detail_view.html'
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
        stock_price_obj = StockPrice.objects.filter(Q(corp_id__exact = id))
        disclosure_name, disclosure_date, disclosure_numbers = self.disclosure_data(id)

        # 공시 데이터를 가져오지 못한 경우
        if disclosure_name is None:
            context['disclosure_data'] = None
        else:
            disclosure_data = zip(disclosure_name, disclosure_date, disclosure_numbers)
            context['disclosure_data'] = disclosure_data
            context['page_obj'] = self.paging_disclosure_data(disclosure_data)

        context['corp_info'] = CorpInfo.objects.get(Q(corp_id__exact = id))
        context['latest_stock_info'] = stock_price_obj.latest('trade_date')
        context['stock_data'] = stock_price_obj
        context['report_data'] = self.recent_report(id)
        
        return context

    # 데이터 추출(사업보고서, 분기보고서)
    def recent_report(self, id):
        y_data = []
        q_data = []
        
        for y in range(1, 5):
            if len(y_data) == 3:
                break
            year = (timezone.now() - timedelta(days=365 * y)).year
            obj = InvestmentIndex.objects.filter(Q(corp_id__exact = id) & Q(year__exact = year) & Q(quarter__exact = 4))
            if obj:
                y_data.append(obj)

            for q in [4, 3, 2, 1]:
                if len(q_data) == 4:
                    break
                obj = InvestmentIndex.objects.filter(Q(corp_id__exact = id) & Q(year__exact = year) & Q(quarter__exact = q))
                if obj:
                    q_data.append(obj)
        
        # 오름차순으로 정렬
        y_data.reverse()
        q_data.reverse()
        
        # 데이터가 부족할 경우 None 삽입
        while True:
            if len(y_data) < 3:
                y_data.append(None)
                continue
            break
        
        while True:
            if len(q_data) < 4:
                q_data.append(None)
                continue
            break
        
        data = [ y_data, q_data ]

        return data

    # 공시 데이터 API 요청
    def disclosure_data(self, id):
        stock_code = CorpId.objects.get(id=id).stock_code
        report_names = []
        report_dates = []
        report_nunbers = []

        if stock_code is None:
            return None, None, None

        url = 'https://opendart.fss.or.kr/api/list.json'
        api_key = get_secret('dart_api_key')
        response = requests.get(url, params={'crtfc_key': api_key, 'stock_code': stock_code, 'bgn_de': 20200101, 'page_count': 100}).json()
        
        if '000' in response['status']:
                for data in response['list']:
                    report_names.append(data['report_nm'])
                    report_dates.append(datetime.strptime(data['rcept_dt'], "%Y%m%d"))
                    report_nunbers.append(data['rcept_no'])
        else:
            return None, None, None
        
        return report_names, report_dates, report_nunbers

    # 공시 데이터 페이징
    def paging_disclosure_data(self, data):
        paginator = Paginator(list(data), 3)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return page_obj
