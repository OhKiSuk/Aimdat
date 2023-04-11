"""
@created at 2023.03.28
@author JSU in Aimdat Team

@modified at 2023.04.11
@author JSU in Aimdat Team
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import ListView

from ..models.corp_summary_financial_statements import \
    CorpSummaryFinancialStatements as FS


class AnalysisView(UserPassesTestMixin, ListView):
    model = FS
    template_name = 'services/analysis_view.html'
    
    def test_func(self):
        if self.request.user.is_admin:
            return False
        
        auth = self.request.user.is_authenticated
        if auth:
            date = self.request.user.expiration_date.date() >= timezone.now().date()
            return auth and date
        
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # 분석 기업 선택 시
        if 'corp_id_list' in self.request.session:
            checked_corp_data = []
            field = ['revenue', 'operating_profit', 'operating_margin', 'net_profit', 'dividend', 'dividend_ratio']
            corp_id_list = self.request.session['corp_id_list']
            corp_year_list = self.request.session['corp_year_list']
            corp_quarter_list = self.request.session['corp_quarter_list']

            # 분석 조건 선택 시
            if 'condition_en_list' in self.request.session and len(self.request.session['condition_en_list']):
                field = self.request.session['condition_en_list']

            for corp_id, corp_year, corp_quarter in zip(corp_id_list, corp_year_list, corp_quarter_list):
                checked_corp_data.append(queryset.filter(Q(corp_id = corp_id) & Q(year = corp_year) & Q(quarter = corp_quarter)).values('corp_id_id', 'corp_id_id__corp_name', 'year', 'quarter', *field))

            return checked_corp_data
        else:
            queryset = []

            return queryset
        
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        remove_field = ['id', 'corp_id', 'disclosure_date', 'year', 'quarter']
        rsi_list = ['per', 'pbr', 'psr', 'ev_ebitda', 'eps', 'bps', 'roe', 'dps']
        fs_list_ko = ['매출액', '영업이익', '순이익', '영업이익률', '순이익률', '부채비율', '매출원가율',\
            '당좌비율', '배당금', '총배당금', '배당수익률', '배당지급률', '배당률', '총부채', '총자산', \
                '총자본', '총차입금', '액면가']

        fs_list_en = [ field.name for field in FS._meta.get_fields() ]
        
        for field in remove_field:
            fs_list_en.remove(field)
            
        for field in rsi_list:
            fs_list_en.remove(field)
        
        corp_data = super().get_queryset().values_list('corp_id_id__corp_name', 'corp_id_id')
        corp_dict = {item[0]: item[1] for item in corp_data}

        context['corp_list'] = corp_dict
        context['corp_name'] = list(set(super().get_queryset().values_list('corp_id_id__corp_name', flat=True)))
        context['graph_fields'] = ['매출액' ,'영업이익', '영업이익률', '당기순이익', '배당금', '배당률']
        context['analysis_data'] = ['revenue', 'operating_profit', 'operating_margin', 'net_profit', 'dividend', 'dividend_ratio']
        context['check_item_fs'] = zip(fs_list_en, fs_list_ko)
        context['check_item_rsi'] = rsi_list
        
        if 'condition_en_list' in self.request.session and len(self.request.session['condition_en_list']):
            context['graph_fields'] = self.request.session['condition_ko_list']
            context['analysis_data'] = self.request.session['condition_en_list']
        
        return context
    
    def post(self, request):
        corp_id_list = []
        corp_year_list = []
        corp_quarter_list = []
        condition_en_list = []
        condition_ko_list = []

        if request.POST.get('checked_corp'):
            for corp in request.POST.getlist('checked_corp'):
                # 전달되는 value를 콤마로 분류하여 저장
                corp_id_list.append(corp.split(', ')[0])
                corp_year_list.append(corp.split(', ')[1])
                corp_quarter_list.append(corp.split(', ')[2][0]) # quarter의 경우 숫자만 저장

            if request.POST.get('checked_item'):
                for name in request.POST.getlist('checked_item'):
                    # 전달되는 value를 콤마로 분류하여 저장
                    condition_en_list.append(name.split(', ')[0])
                    condition_ko_list.append(name.split(', ')[1])

            request.session['corp_id_list'] = corp_id_list
            request.session['corp_year_list'] = corp_year_list
            request.session['corp_quarter_list'] = corp_quarter_list
            request.session['condition_en_list'] = condition_en_list
            request.session['condition_ko_list'] = condition_ko_list
        
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        
        return render(request, 'services/analysis_view.html', context=context)
