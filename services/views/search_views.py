"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.03.20
@author JSU in Aimdat Team
"""

from django.views.generic.list import ListView
from django.db.models import Q
from django.shortcuts import render
from ..models.corp_summary_financial_statements import CorpSummaryFinancialStatements as fs
from decimal import Decimal
class SearchView(ListView):
    model = fs
    template_name = 'services/search_view.html'
    paginate_by = 100
    q = Q()
    name_en = []
    name_ko = []
    min = []
    max = []
    condition_en = ['revenue', 'operating_profit', 'net_profit', 'operating_margin',\
        'net_profit_margin', 'debt_ratio', 'cost_of_sales_ratio', 'quick_ratio', 'dividend',\
            'total_dividend', 'dividend_yield', 'dividend_payout_ratio', 'dividend_ratio',\
                'per', 'pbr', 'psr', 'ev_ebitda', 'ev_per_ebitda', 'eps', 'bps', 'roe', 'dps',\
                    'total_debt', 'total_asset', 'total_capital', 'borrow_debt', 'face_value']
    condition_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
        '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', 'PER', 'PBR', 'PSR',\
            'EV_EBITDA', 'EV_PER_EBITDA', 'EPS', 'BPS', 'ROE', 'DPS', '총부채', '총자산', '총자본',\
                '총차입금', '액면가']
    fs_list_en = ['revenue', 'operating_profit', 'net_profit', 'operating_margin',\
        'net_profit_margin', 'debt_ratio', 'cost_of_sales_ratio', 'quick_ratio', 'dividend',\
            'total_dividend', 'dividend_yield', 'dividend_payout_ratio', 'dividend_ratio',\
                'total_debt', 'total_asset', 'total_capital', 'borrow_debt', 'face_value']
    fs_list_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
        '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', '총부채', '총자산', \
            '총자본', '총차입금', '액면가']
    rsi_list_upper = ['PER', 'PBR', 'PSR', 'EV_EBITDA', 'EV_PER_EBITDA', 'EPS', 'BPS', 'ROE', 'DPS']
    rsi_list_lower = ['per', 'pbr', 'psr', 'ev_ebitda', 'ev_per_ebitda', 'eps', 'bps', 'roe', 'dps']
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Session이 값이 있을 경우
        if 'name_en' in self.request.session:
            self.name_en = self.request.session['name_en']
            self.name_ko = self.request.session['name_ko']
            self.min = self.request.session['min']
            self.max = self.request.session['max']            
            
            for condition, min_data, max_data in zip(self.name_en, self.min, self.max):
                self.q &= Q(**{condition+'__range': (Decimal(min_data), Decimal(max_data))})
            qs = qs.filter(self.q)
            return qs
        else:
            return qs

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        context['table_column'] = self.condition_ko
        context['input_item_fs'] = zip(self.fs_list_en, self.fs_list_ko)
        context['input_item_rsi'] = zip(self.rsi_list_upper, self.rsi_list_lower)
        context['filter_item_fs'] = zip(self.fs_list_en, self.fs_list_ko)
        context['filter_item_rsi'] = zip(self.rsi_list_upper, self.rsi_list_lower)
        
        # Session이 값이 있을 경우
        if 'name_en' in self.request.session:
            context['applied_filter_list'] = zip(self.name_en, self.name_ko, self.min, self.max)
            context['applied_filter_modal'] = zip(self.name_en, self.name_ko, self.min, self.max)
            context['applied_input_data'] = zip(self.name_en, self.min, self.max)
        return context
    
    def post(self, request):
        self.name_en = []
        self.name_ko = []
        self.min = []
        self.max = []
        
        # 조건 데이터 추출
        for en, ko in zip(self.condition_en, self.condition_ko):
            if request.POST.get(en+'_max'):
                min_data = request.POST.get(en+'_min')
                max_data = request.POST.get(en+'_max')
                self.name_en.append(en)
                self.name_ko.append(ko)
                self.min.append(min_data)
                self.max.append(max_data)

        request.session['name_en'] = self.name_en
        request.session['name_ko'] = self.name_ko
        request.session['min'] = self.min
        request.session['max'] = self.max
        
        context = self.get_context_data()
        return render(request, 'services/search_view.html', context)
