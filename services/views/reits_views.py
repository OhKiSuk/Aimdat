"""
@created at 2023.08.11
@author OKS in Aimdat Team

@modified at 2023.08.23
@author OKS in Aimdat Team
"""
import requests

from config.settings.base import get_secret
from datetime import (
    datetime, 
    timedelta
)
from django.core.paginator import Paginator
from django.views.generic import (
    ListView,
    DetailView
)
from django.db.models import (
    DateField,
    F
)
from django.db.models.functions import Cast

from ..models.corp_info import CorpInfo
from ..models.reits_inquiry import ReitsInquiry
from ..models.stock_price import StockPrice

class ReitsHomeView(ListView):
    """
    Reits 정보 홈페이지
    """
    template_name = 'services/reits/reits_home.html'
    model = ReitsInquiry
    ordering = ['corp_id__corp_name']
    
class ReitsInquriyView(DetailView):
    """
    리츠 정보 상세 뷰
    """
    template_name = 'services/reits/reits_inquiry.html'
    model = ReitsInquiry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stock_price_obj = StockPrice.objects.filter(corp_id_id=self.object.corp_id.id).annotate(
            date_field=Cast(F('trade_date'), output_field=DateField())
        ).order_by('date_field')

        # 윤년 계산
        if (datetime.now().year % 4 == 0 and datetime.now().year % 100 != 0) or datetime.now().year % 400 == 0:
            week_52 = (datetime.now() - timedelta(days=366)).strftime('%Y-%m-%d')
        else:
            week_52 = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        context['corp_info'] = CorpInfo.objects.get(corp_id_id=self.object.corp_id.id)
        context['stock_price'] = StockPrice.objects.filter(corp_id_id=self.object.corp_id.id)
        context['latest_stock_info'] = stock_price_obj.latest('date_field')
        context['week_52_price'] = stock_price_obj.get(trade_date__exact = str(week_52)) if stock_price_obj.filter(trade_date__exact = str(week_52)).exists() else None

        # 공시정보
        context['page_obj'] = self.paging_disclosure_data(self.disclosure_data())

        # 투자자산 정보 및 차입금 정보
        investment_assets_info_keys = ['asset_name', 'asset_division', 'area', 'rental_rate', 'wale']
        borrowed_info_keys = ['institution_name', 'borrowed_division', 'amount', 'due_date', 'interest_rate']

        investment_assets_info_data = []
        for obj in self.object.investment_assets_info:
            sorted_obj = [(key,obj[key]) for key in investment_assets_info_keys]
            investment_assets_info_data.append(sorted_obj)

        borrowed_info_data = []
        for obj in self.object.borrowed_info:
            sorted_obj = [(key,obj[key]) for key in borrowed_info_keys]
            borrowed_info_data.append(sorted_obj)

        context['investment_assets_info'] = investment_assets_info_data
        context['borrowed_info'] = borrowed_info_data

        return context
    
    # 공시 데이터 API 요청
    def disclosure_data(self):
        stock_code = self.object.corp_id.stock_code
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