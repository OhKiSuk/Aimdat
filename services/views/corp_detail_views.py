"""
@created at 2023.03.22
@author JSU in Aimdat Team

@modified at 2023.04.07
@author JSU in Aimdat Team

@modified at 2023.04.09
@author JSU in Aimdat Team
"""

import json
from datetime import datetime, timedelta

import requests
from django.apps import apps
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView

from config.settings.base import get_secret

from ..models.corp_id import CorpId
from ..models.corp_info import CorpInfo
from ..models.corp_summary_financial_statements import \
    CorpSummaryFinancialStatements as FS
from ..models.stock_price import StockPrice


class CorpDetailView(UserPassesTestMixin, DetailView):
    model = CorpId
    template_name = 'services/corp_detail_view.html'
    context_object_name = 'corp_id'
    pk_url_kwarg = 'id'
    
    def test_func(self):
        auth = self.request.user.is_authenticated
        if auth:
            date = self.request.user.expiration_date.date() >= timezone.now().date()
            return auth and date
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs.get(self.pk_url_kwarg)
        disclosure_name, disclosure_date, disclosure_no = self.get_disclosure_data(id)

        if 'No data' in disclosure_name:
            context['disclosure_data'] = ''
        else:
            disclosure_data = zip(disclosure_name, disclosure_date, disclosure_no)
            context['disclosure_data'] = disclosure_data
            context['page_obj'] = self.paging_disclosure_data(disclosure_data)


        context['corp_info'] = CorpInfo.objects.get(corp_id=id)
        context['stock_price'] = StockPrice.objects.filter(corp_id=id).latest('trade_date')
        context['price_graph_data'] = StockPrice.objects.filter(corp_id=id).values('trade_date', 'open_price', 'high_price', 'low_price', 'close_price')
        context['trade_graph_data'] = StockPrice.objects.filter(corp_id=id).values('trade_date', 'trade_quantity')
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
            obj = FS.objects.filter(corp_id=id, year=year, quarter=4)
            if obj:
                y_data.append(obj)

            for q in [4, 3, 2, 1]:
                if len(q_data) == 4:
                    break
                obj = FS.objects.filter(corp_id=id, year=year, quarter=q)
                if obj:
                    q_data.append(obj)
        
        # 최신 값을 뒤로 정렬
        y_data.reverse()
        q_data.reverse()
        
        # 데이터가 3개 미만일 경우 빈 값 삽입
        while True:
            if len(y_data) < 3:
                y_data.append(' ')
                continue
            break
        
        while True:
            if len(q_data) < 4:
                q_data.append(' ')
                continue
            break
        
        data = [y_data, q_data]
        return data

    # 공시 데이터
    def get_disclosure_data(self, id):
        app_config = apps.get_app_config('services')
        key = CorpId.objects.get(id=id).stock_code
        report_names = []
        report_dates = []
        report_no = []
        
        if key is None:
            return 'No data', '', ''

        with open(app_config.path + '/corp_code.json', 'r') as f:
            data = json.load(f)
        
        if key in data:
            corp_code = data[key]

        url = 'https://opendart.fss.or.kr/api/list.json'
        api_key = get_secret('dart_api_key')
        response = requests.get(url, params={'crtfc_key': api_key, 'corp_code': corp_code, 'bgn_de': 20000101, 'page_count': 5000}).json()
        if '000' in response['status']:
            for data in response['list']:
                report_names.append(data['report_nm'])
                report_dates.append(datetime.strptime(data['rcept_dt'], "%Y%m%d"))
                report_no.append(data['rcept_no'])
        else:
            return 'No data', '', ''
        
        return report_names, report_dates, report_no

    # 공시 데이터 페이징
    def paging_disclosure_data(self, data):
        paginator = Paginator(list(data), 3)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj
