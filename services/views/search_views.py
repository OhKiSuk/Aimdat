"""
@created at 2023.03.15
@author JSU in Aimdat Team

@modified at 2023.03.20
@author JSU in Aimdat Team

@modified at 2023.03.28
@author JSU in Aimdat Team

@modified at 2023.03.30
@author JSU in Aimdat Team

@modified at 2023.04.05
@author JSU in Aimdat Team

@modified at 2023.04.07
@author JSU in Aimdat Team

@modified at 2023.04.09
@author JSU in Aimdat Team
"""

from decimal import Decimal

from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic.list import ListView

from ..models.corp_summary_financial_statements import \
    CorpSummaryFinancialStatements as FS


class SearchView(UserPassesTestMixin, ListView):
    model = FS
    template_name = 'services/search_view.html'
    paginate_by = 100
    
    def test_func(self):
        auth = self.request.user.is_authenticated
        if auth:
            date = self.request.user.expiration_date.date() >= timezone.now().date()
            return auth and date
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = Q()

        # Session에 기업명 값이 있을 경우
        if 'corp' in self.request.session:
            for name in self.request.session['corp']:
                q |= Q(corp_id_id__corp_name__icontains=name)

        # Session에 연, 분기 값이 있을 경우
        if 'year' in self.request.session:
            q &= Q(year=self.request.session['year'])
        if 'quarter' in self.request.session:
            q &= Q(quarter=self.request.session['quarter'])

        # Session에 조건 값이 있을 경우
        if 'name_en' in self.request.session and len(self.request.session['name_en']):
            name_en = self.request.session['name_en']
            min = self.request.session['min']
            max = self.request.session['max']            
            
            for condition, min_data, max_data in zip(name_en, min, max):
                q &= Q(**{condition+'__range': (Decimal(min_data), Decimal(max_data))})
            queryset = queryset.filter(q).values('corp_id', 'year', 'quarter', *name_en, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset
        else:
            name_en = ['revenue', 'operating_profit', 'operating_margin', 'net_profit', 'dividend', 'dividend_ratio']
            queryset = queryset.filter(q).values('corp_id', 'year', 'quarter', *name_en, 'corp_id_id__corp_name', 'corp_id_id__corp_country', 'corp_id_id__corp_sectors', 'corp_id_id__corp_market')
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rsi_list_lower = ['per', 'pbr', 'psr', 'ev_ebitda', 'eps', 'bps', 'roe', 'dps']
        rsi_list_upper = [word.upper() for word in rsi_list_lower]
        fs_list_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
            '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', '총부채', '총자산', \
                '총자본', '총차입금', '액면가']
        
        fs_list_en = [field.name for field in FS._meta.get_fields()]
        remove_field = ['id', 'corp_id', 'disclosure_date', 'year', 'quarter']
        
        for field in remove_field:
            fs_list_en.remove(field)
            
        for field in rsi_list_lower:
            fs_list_en.remove(field)
        
        context['corp_name'] = list(set(super().get_queryset().values_list('corp_id_id__corp_name', flat=True)))
        context['table_column'] = ['매출액' ,'영업이익', '영업이익률', '당기순이익', '배당금', '배당률']
        context['fields'] = ['revenue', 'operating_profit', 'operating_margin', 'net_profit', 'dividend', 'dividend_ratio']
        context['input_item_fs'] = zip(fs_list_en, fs_list_ko)
        context['input_item_rsi'] = zip(rsi_list_upper, rsi_list_lower)
        context['filter_item_fs'] = zip(fs_list_en, fs_list_ko)
        context['filter_item_rsi'] = zip(rsi_list_upper, rsi_list_lower)

        # Session에 기업명 값이 있을 경우
        if 'corp' in self.request.session:
            context['corp'] = self.request.session['corp']

        # Session에 연, 분기 값이 있을 경우
        if 'year' in self.request.session:
            context['year'] = self.request.session['year']
        if 'quarter' in self.request.session:
            context['quarter'] = self.request.session['quarter']
        
        # Session에 조건 값이 있을 경우
        if 'name_en' in self.request.session and len(self.request.session['name_en']):
            context['table_column'] = self.request.session['name_ko']
            context['fields'] = [*self.request.session['name_en']]
            context['applied_filter_list'] = zip(self.request.session['name_en'], self.request.session['name_ko'], self.request.session['min'], self.request.session['max'])
            context['applied_filter_modal'] = zip(self.request.session['name_en'], self.request.session['name_ko'], self.request.session['min'], self.request.session['max'])
            context['applied_input_data'] = zip(self.request.session['name_en'], self.request.session['min'], self.request.session['max'])

        return context
    
    def post(self, request):
        name_en = []
        name_ko = []
        min = []
        max = []
        fields = [field.name for field in FS._meta.get_fields()]
        remove_field = ['id', 'corp_id', 'disclosure_date', 'year', 'quarter']
        condition_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
        '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', 'PER', 'PBR', 'PSR',\
            'EV_EBITDA', 'EV_PER_EBITDA', 'EPS', 'BPS', 'ROE', 'DPS', '총부채', '총자산', '총자본',\
                '총차입금', '액면가']
        
        for field in remove_field:
            fields.remove(field)
        
        # 조건
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

        # 연, 분기
        if request.POST.get('year'):
            request.session['year'] = request.POST.get('year')
        else:
            request.session.pop('year', None)
        if request.POST.get('quarter'):
            request.session['quarter'] = request.POST.get('quarter')[0]
        else:
            request.session.pop('quarter', None)

        # 기업명
        if request.POST.get('corp'):
            request.session['corp'] = request.POST.get('corp')
        else:
            request.session.pop('corp', None)

        
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return render(request, 'services/search_view.html', context=context)
