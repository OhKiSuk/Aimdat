"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.03.20
@author JSU in Aimdat Team
"""

from datetime import datetime
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from ..models.corp_summary_financial_statements import CorpSummaryFinancialStatements as fs
from decimal import Decimal

class SearchView(UserPassesTestMixin, ListView):
    model = fs
    template_name = 'services/search_view.html'
    paginate_by = 100
    q = Q()
    
    def test_func(self):
        user = self.request.user
        date = user.expiration_date if user.is_authenticated else None
        return date and date >= datetime.now()
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse('account:login'))
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Session이 값이 있을 경우
        if 'name_en' in self.request.session:
            name_en = self.request.session['name_en']
            min = self.request.session['min']
            max = self.request.session['max']            
            
            for condition, min_data, max_data in zip(name_en, min, max):
                self.q &= Q(**{condition+'__range': (Decimal(min_data), Decimal(max_data))})
            qs = qs.filter(self.q)
            return qs
        else:
            return qs

    def get_context_data(self, **kwargs):
        self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        rsi_list_lower = ['per', 'pbr', 'psr', 'ev_ebitda', 'ev_per_ebitda', 'eps', 'bps', 'roe', 'dps']
        rsi_list_upper = [word.upper() for word in rsi_list_lower]
        condition_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
        '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', 'PER', 'PBR', 'PSR',\
            'EV_EBITDA', 'EV_PER_EBITDA', 'EPS', 'BPS', 'ROE', 'DPS', '총부채', '총자산', '총자본',\
                '총차입금', '액면가']
        fs_list_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
            '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', '총부채', '총자산', \
                '총자본', '총차입금', '액면가']
        
        fs_list_en = [field.name for field in fs._meta.get_fields()]
        remove_field = ['id', 'corp_id', 'disclosure_date', 'year', 'month']
        
        for field in remove_field:
            fs_list_en.remove(field)
            
        for field in rsi_list_lower:
            fs_list_en.remove(field)
        
        context['table_column'] = condition_ko
        context['input_item_fs'] = zip(fs_list_en, fs_list_ko)
        context['input_item_rsi'] = zip(rsi_list_upper, rsi_list_lower)
        context['filter_item_fs'] = zip(fs_list_en, fs_list_ko)
        context['filter_item_rsi'] = zip(rsi_list_upper, rsi_list_lower)
        
        # Session이 값이 있을 경우
        if 'name_en' in self.request.session:
            context['applied_filter_list'] = zip(self.request.session['name_en'], self.request.session['name_ko'], self.request.session['min'], self.request.session['max'])
            context['applied_filter_modal'] = zip(self.request.session['name_en'], self.request.session['name_ko'], self.request.session['min'], self.request.session['max'])
            context['applied_input_data'] = zip(self.request.session['name_en'], self.request.session['min'], self.request.session['max'])
        return context
    
    def post(self, request):
        name_en = []
        name_ko = []
        min = []
        max = []
        fields = [field.name for field in fs._meta.get_fields()]
        remove_field = ['id', 'corp_id', 'disclosure_date', 'year', 'month']
        condition_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
        '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', 'PER', 'PBR', 'PSR',\
            'EV_EBITDA', 'EV_PER_EBITDA', 'EPS', 'BPS', 'ROE', 'DPS', '총부채', '총자산', '총자본',\
                '총차입금', '액면가']
        
        for field in remove_field:
            fields.remove(field)
        
        # 조건 데이터 추출
        for en, ko in zip(fields, condition_ko):
            if request.POST.get(en+'_max'):
                min_data = request.POST.get(en+'_min')
                max_data = request.POST.get(en+'_max')
                name_en.append(en)
                name_ko.append(ko)
                min.append(min_data)
                max.append(max_data)

        request.session['name_en'] = name_en
        request.session['name_ko'] = name_ko
        request.session['min'] = min
        request.session['max'] = max
        
        context = self.get_context_data()
        return render(request, 'services/search_view.html', context)
