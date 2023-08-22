"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.08.10
@author OKS in Aimdat Team
"""
import json
import logging

from decimal import Decimal
from django.db.models import (
    Q,
    Max,
    Min
)
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.list import ListView

from ..models.investment_index import InvestmentIndex

LOGGER = logging.getLogger(__name__)

class SearchView(ListView):
    """
    기업 조건 검색 뷰
    """
    model = InvestmentIndex
    template_name = 'services/search_view.html'
    paginate_by = 20
    
    def get_ordering(self):
        ordering = json.loads(self.request.GET.get('ordering', '"corp_id__corp_name"'))

        if ordering == 'corp_name':
             ordering = 'corp_id__corp_name'
        elif ordering == '-corp_name':
            ordering = '-corp_id__corp_name'

        return ordering
    
    def paginate_queryset(self, queryset, page_size):
        if 'page' in self.request.GET:
            paginator = self.get_paginator(
                queryset,
                page_size*int(self.request.GET['page']),
                orphans=self.get_paginate_orphans(),
                allow_empty_first_page=self.get_allow_empty(),
            )

            page = paginator.page(1)
            return (paginator, page, page.object_list, page.has_other_pages())

        return super().paginate_queryset(queryset, page_size)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = Q()

        # 지표 목록
        index_list = [field.name for field in InvestmentIndex._meta.fields if field.name not in ['id', 'corp_id', 'year', 'quarter', 'fs_type']]

        # DB에 저장된 최근 년도 및 분기 값
        recent_year = InvestmentIndex.objects.all().aggregate(recent_year=Max('year'))['recent_year']
        recent_quarter = InvestmentIndex.objects.filter(year=recent_year).aggregate(recent_quarter=Max('quarter'))['recent_quarter']

        # 조건식에 기업명 값이 있을 경우 설정(기본 값: 없음)
        if 'corp_name' in self.request.session:
            if str(self.request.session['corp_name']).isdigit() and len(self.request.session['corp_name']) == 6:
                q &= Q(corp_id__stock_code__icontains=self.request.session['corp_name'])
            else:
                q &= Q(corp_id__corp_name__icontains=self.request.session['corp_name'])

        # 조건식에 재무제표 년도, 분기, 유형 값 설정(기본 값: DB에 저장된 최근 별도 재무제표 목록)
        if 'year' in self.request.session:
            q &= Q(year__exact=self.request.session['year'])
        else:
            q &= Q(year__exact=recent_year)

        if 'quarter' in self.request.session:
            q &= Q(quarter__exact=self.request.session['quarter'])
        else:
            q &= Q(quarter__exact=recent_quarter)

        if 'fs_type' in self.request.session:
            q &= Q(fs_type__exact=self.request.session['fs_type'])
        else:
            q &= Q(fs_type__exact=5)

        # 조건식에 조건 값이 있을 경우 설정(기본 값: 매출액, 영업이익, 당기순이익, 유동비율, 부채비율, 배당금, 배당률)
        if 'index' in self.request.session and len(self.request.session['index']) > 0:
            indexes = self.request.session['index']

            indexes_en = []
            for index_name in self.request.session['index']:
                for index in index_list:
                    if index == index_name:
                        min = indexes[index_name]['min']
                        max = indexes[index_name]['max']

                        if max == '이상':
                            q &= Q(**{index+'__gte': Decimal(min)})
                        elif min == '이하':
                            q &= Q(**{index+'__lte': Decimal(max)})
                        elif min == '전체' and max == '전체':
                            # 모델 값에 저장 된 가장 작은 수 및 가장 큰 수
                            investment_index_max = InvestmentIndex.objects.aggregate(max_number=Max(index))['max_number']
                            investment_index_min = InvestmentIndex.objects.aggregate(min_number=Min(index))['min_number']

                            q &= Q(**{index+'__range': (Decimal(investment_index_min), Decimal(investment_index_max))})
                        else:
                            q &= Q(**{index+'__range': (Decimal(min), Decimal(max))})
                    
                        indexes_en.append(index)                     

            queryset = queryset.filter(q)\
                .values('corp_id', 'year', 'quarter', *indexes_en, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset
        else:
            default_index = ['revenue', 'operating_profit', 'operating_margin']

            for index_name in default_index:
                # 모델 값에 저장 된 가장 작은 수 및 가장 큰 수
                investment_index_max = InvestmentIndex.objects.aggregate(max_number=Max(index_name))['max_number']
                investment_index_min = InvestmentIndex.objects.aggregate(min_number=Min(index_name))['min_number']

                q &= Q(**{index_name+'__range': (Decimal(investment_index_min), Decimal(investment_index_max))})

            queryset = queryset.filter(q)\
                .values('corp_id', 'year', 'quarter', *default_index, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # DB에 저장된 최근 년도 및 분기 값
        recent_year = InvestmentIndex.objects.all().aggregate(recent_year=Max('year'))['recent_year']
        recent_quarter = InvestmentIndex.objects.filter(year=recent_year).aggregate(recent_quarter=Max('quarter'))['recent_quarter']

        # 지표 구분
        account_index = [
            'revenue', 
            'operating_profit', 
            'net_profit',
            'total_assets',
            'total_debt',
            'total_capital',
            'operating_cash_flow',
            'investing_cash_flow',
            'financing_cash_flow',
        ]
        safety_index = [
            'current_ratio',
            'quick_ratio',
            'debt_ratio',
            'interest_coverage_ratio'
        ]
        profitability_index = [
            'cost_of_sales_ratio',
            'gross_profit_margin',
            'operating_margin',
            'net_profit_margin',
            'roic',
            'roe',
            'roa'
        ]
        activity_index = [
            'total_assets_turnover',
            'inventory_turnover',
            'accounts_receivables_turnover',
            'accounts_payable_turnover',
            'working_capital_requirement',
            'working_capital_once'
        ]
        growth_index = [
            'revenue_growth',
            'operating_profit_growth',
            'net_profit_growth',
            'net_worth_growth',
            'assets_growth'
        ]
        investment_index = [
            'per',
            'pbr',
            'psr',
            'eps',
            'bps',
            'ev_ebitda',
            'ev_ocf',
        ]
        dividend_index = ['dividend', 'dividend_ratio', 'dividend_payout_ratio', 'dps']

        # Session에 기업명 값이 있을 경우
        if 'corp_name' in self.request.session:
            context['corp_name'] = self.request.session['corp_name']

        # Session에 재무제표 년도, 분기, 유형 값이 있을 경우(기본 값: 당년도 최근 분기 별도 재무제표)
        if 'year' in self.request.session:
            context['year'] = self.request.session['year']
        else:
            context['year'] = recent_year

        if 'quarter' in self.request.session:
            context['quarter'] = self.request.session['quarter']
        else:
            context['quarter'] = recent_quarter

        if 'fs_type' in self.request.session:
            context['fs_type'] = self.request.session['fs_type']
        else:
            context['fs_type'] = 5
        
        # Session에 조건 값이 존재할 경우(없으면 기본 값 검색: 매출액, 영업이익, 당기순이익, 유동비율, 부채비율, 배당금, 배당률)
        if 'index' in self.request.session and len(self.request.session['index']) > 0:
            context['index'] = self.request.session['index']
        else:
            context['index'] = {
                'revenue': {'min': '전체', 'max': '전체'},
                'operating_profit': {'min': '전체', 'max': '전체'},
                'operating_margin': {'min': '전체', 'max': '전체'}
            }

        context['account_index'] = account_index
        context['safety_index'] = safety_index
        context['profitability_index'] = profitability_index
        context['activity_index'] = activity_index
        context['growth_index'] = growth_index
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
            recent_year = InvestmentIndex.objects.all().aggregate(recent_year=Max('year'))['recent_year']
            recent_quarter = InvestmentIndex.objects.filter(year=recent_year).aggregate(recent_quarter=Max('quarter'))['recent_quarter']

            if indexes:
                index_session = {}
                for index_name in indexes:
                    if index_name == 'corp_name':
                        self.request.session['corp_name'] = indexes['corp_name']
                    elif index_name == 'fs_options':
                        if indexes['fs_options']['year'] == '' or indexes['fs_options']['quarter'] == '' or indexes['fs_options']['fs_type'] == '':
                            self.request.session['year'] = recent_year
                            self.request.session['quarter'] = recent_quarter
                            self.request.session['fs_type'] = 5
                        else:
                            self.request.session['year'] = indexes['fs_options']['year']
                            self.request.session['quarter'] = indexes['fs_options']['quarter']
                            self.request.session['fs_type'] = indexes['fs_options']['fs_type']
                    else:
                        index_session[index_name] = indexes[index_name]
                    
                if 'corp_name' not in indexes.keys():
                    if 'corp_name' in self.request.session:
                        del self.request.session['corp_name']
                if 'fs_options' not in indexes.keys():
                    if 'year' in self.request.session and 'quarter' in self.request.session and 'fs_type' in self.request.session:
                        self.request.session['year'] = recent_year
                        self.request.session['quarter'] = recent_quarter
                        self.request.session['fs_type'] = 5
                
                self.request.session['index'] = index_session
                # U101 로깅
                LOGGER.info('[U101] 검색에 사용한 정보. {}'.format(indexes))

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        
        return render(request, 'services/search_view.html', context=context)
    
    def get(self, request):

        if request.GET.get('page') or request.GET.get('ordering'):
            if not self.request.user.is_authenticated:
                return HttpResponse('로그인이 필요한 서비스입니다.', status=500)
        
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return render(request, self.template_name, context=context)