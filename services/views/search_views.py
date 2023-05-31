"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.05.27
@author OKS in Aimdat Team
"""
import datetime
import json

from decimal import Decimal
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import (
    Q,
    Max,
    Min
)
from django.shortcuts import (
    redirect, 
    render
)
from django.utils import timezone
from django.views.generic.list import ListView

from ..models.investment_index import InvestmentIndex

class SearchView(UserPassesTestMixin, ListView):
    """
    기업 조건 검색 뷰
    """
    model = InvestmentIndex
    template_name = 'services/search_view.html'
    paginate_by = 100
    ordering = ['corp_id__corp_name']
    
    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False
            if self.request.user.expiration_date.date() >= timezone.now().date():
                return True
            
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = Q()

        # 지표 목록
        index_dict_list = {
            '매출액': 'revenue',
            '영업이익': 'operating_profit',
            '당기순이익': 'net_profit',
            '매출원가': 'cost_of_sales',
            '매출원가율': 'cost_of_sales_ratio',
            '영업이익률': 'operating_margin',
            '순이익률': 'net_profit_margin',
            'ROE': 'roe',
            'ROA': 'roa',
            '유동비율': 'current_ratio',
            '당좌비율': 'quick_ratio',
            '부채비율': 'debt_ratio',
            'PER': 'per',
            'PBR': 'pbr',
            'PSR': 'psr',
            'EPS': 'eps',
            'BPS': 'bps',
            'EV/EBITDA': 'ev_ebitda',
            'EV/OCF': 'ev_ocf',
            '배당금': 'dividend',
            '배당률': 'dividend_ratio',
            '배당성향': 'dividend_payout_ratio',
            'DPS': 'dps'
        }

        # 조건식에 기업명 값이 있을 경우 설정(기본 값: 없음)
        if 'corp_name' in self.request.session:
            if str(self.request.session['corp_name']).isdigit() and len(self.request.session['corp_name']) == 6:
                q &= Q(corp_id__stock_code__icontains=self.request.session['corp_name'])
            else:
                q &= Q(corp_id__corp_name__icontains=self.request.session['corp_name'])

        # 조건식에 재무제표 년도, 분기, 유형 값 설정(기본 값: 당년도 최근 분기 별도 재무제표)
        if 'year' in self.request.session:
            q &= Q(year__exact=self.request.session['year'])
        else:
            q &= Q(year__exact=datetime.datetime.now().year)

        if 'quarter' in self.request.session:
            q &= Q(quarter__exact=self.request.session['quarter'])
        else:
            quarter = InvestmentIndex.objects.filter(year=datetime.datetime.now().year).aggregate(max_value=Max('quarter'))['max_value']
            q &= Q(quarter__exact=quarter)

        if 'fs_type' in self.request.session:
            q &= Q(fs_type__exact=self.request.session['fs_type'])
        else:
            q &= Q(fs_type__exact=5)

        # 조건식에 조건 값이 있을 경우 설정(기본 값: 매출액, 영업이익, 당기순이익, 유동비율, 부채비율, 배당금, 배당률)
        if 'index' in self.request.session and len(self.request.session['index']) > 0:
            indexes = self.request.session['index']

            indexes_en = []
            for index_name in self.request.session['index']:
                for index_name_ko, index_name_en in index_dict_list.items():
                    if index_name_ko == index_name:
                        min = indexes[index_name]['min']
                        max = indexes[index_name]['max']

                        if max == '이상':
                            q &= Q(**{index_name_en+'__gte': Decimal(min)})
                        elif min == '이하':
                            q &= Q(**{index_name_en+'__lte': Decimal(max)})
                        elif min == '전체' and max == '전체':
                            # 모델 값에 저장 된 가장 작은 수 및 가장 큰 수
                            investment_index_max = InvestmentIndex.objects.aggregate(max_number=Max(index_name_en))['max_number']
                            investment_index_min = InvestmentIndex.objects.aggregate(min_number=Min(index_name_en))['min_number']

                            q &= Q(**{index_name_en+'__range': (Decimal(investment_index_min), Decimal(investment_index_max))})
                        else:
                            q &= Q(**{index_name_en+'__range': (Decimal(min), Decimal(max))})
                    
                        indexes_en.append(index_name_en)                     
            
            queryset = queryset.filter(q).values('corp_id', 'year', 'quarter', *indexes_en, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset
        else:
            default_index = ['revenue', 'operating_profit', 'net_profit', 'current_ratio', 'debt_ratio', 'dividend', 'dividend_ratio']

            for index_name in default_index:
                # 모델 값에 저장 된 가장 작은 수 및 가장 큰 수
                investment_index_max = InvestmentIndex.objects.aggregate(max_number=Max(index_name))['max_number']
                investment_index_min = InvestmentIndex.objects.aggregate(min_number=Min(index_name))['min_number']

                q &= Q(**{index_name+'__range': (Decimal(investment_index_min), Decimal(investment_index_max))})

            queryset = queryset.filter(q).values('corp_id', 'year', 'quarter', *default_index, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 지표 구분
        account_index = {
            '매출액': 'revenue',
            '영업이익': 'operating_profit',
            '당기순이익': 'net_profit',
            '매출원가': 'cost_of_sales'
        }
        investment_index = {
            '매출원가율': 'cost_of_sales_ratio',
            '영업이익률': 'operating_margin',
            '순이익률': 'net_profit_margin',
            'ROE': 'roe',
            'ROA': 'roa',
            '유동비율': 'current_ratio',
            '당좌비율': 'quick_ratio',
            '부채비율': 'debt_ratio',
            'PER': 'per',
            'PBR': 'pbr',
            'PSR': 'psr',
            'EPS': 'eps',
            'BPS': 'bps',
            'EV/EBITDA': 'ev_ebitda',
            'EV/OCF': 'ev_ocf',
        }
        dividend_index = {
            '배당금': 'dividend',
            '배당률': 'dividend_ratio',
            '배당성향': 'dividend_payout_ratio',
            'DPS': 'dps'
        }

        # Session에 기업명 값이 있을 경우
        if 'corp_name' in self.request.session:
            context['corp_name'] = self.request.session['corp_name']

        # Session에 재무제표 년도, 분기, 유형 값이 있을 경우(기본 값: 당년도 최근 분기 별도 재무제표)
        if 'year' in self.request.session:
            context['year'] = self.request.session['year']
        else:
            context['year'] = datetime.datetime.now().year

        if 'quarter' in self.request.session:
            context['quarter'] = self.request.session['quarter']
        else:
            context['quarter'] = InvestmentIndex.objects.filter(year=datetime.datetime.now().year).aggregate(max_value=Max('quarter'))

        if 'fs_type' in self.request.session:
            context['fs_type'] = self.request.session['fs_type']
        else:
            context['fs_type'] = 5
        
        # Session에 조건 값이 존재할 경우(없으면 기본 값 검색: 매출액, 영업이익, 당기순이익, 유동비율, 부채비율, 배당금, 배당률)
        if 'index' in self.request.session and len(self.request.session['index']) > 0:
            context['index'] = self.request.session['index']
        else:
            context['index'] = {
                '매출액': {'min': '전체', 'max': '전체'},
                '영업이익': {'min': '전체', 'max': '전체'},
                '당기순이익': {'min': '전체', 'max': '전체'},
                '유동비율': {'min': '전체', 'max': '전체'},
                '부채비율': {'min': '전체', 'max': '전체'},
                '배당금': {'min': '전체', 'max': '전체'},
                '배당률': {'min': '전체', 'max': '전체'},
            }

        context['account_index'] = account_index
        context['investment_index'] = investment_index
        context['dividend_index'] = dividend_index

        return context
    
    def post(self, request):
        if request.body.decode('utf-8') == 'reset' or request.body.decode('utf-8') == '{}':
            # 세션 초기화
            remove_session_keys = ['index', 'corp_name', 'year', 'quarter', 'fs_type']
            session_keys = request.session.keys()
            for key in remove_session_keys:
                if key in session_keys:
                    del self.request.session[key]
        else:
            indexes = json.loads(request.body.decode('utf-8'))

            if indexes:
                index_session = {}
                for index_name in indexes:
                    if index_name == 'corp_name':
                        self.request.session['corp_name'] = indexes['corp_name']
                    elif index_name == 'fs_options':
                        self.request.session['year'] = indexes['fs_options']['year']
                        self.request.session['quarter'] = indexes['fs_options']['quarter']
                        self.request.session['fs_type'] = indexes['fs_options']['fs_type']
                    else:
                        index_session[index_name] = indexes[index_name]
                    
                self.request.session['index'] = index_session

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        
        return render(request, 'services/search_view.html', context=context)
