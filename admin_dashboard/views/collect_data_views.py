"""
author: cslee

@modified at 2023.04.17
@author OKS in Aimdat Team
"""
from django.db.utils import ProgrammingError
from django.shortcuts import render
from django.views.generic import TemplateView, View
from admin_dashboard.modules.collect.corp import collect_corp
from admin_dashboard.modules.collect.stock_price import collect_stock_price
from admin_dashboard.modules.collect.summary_financial_statements import collect_summary_finaicial_statements

from ..models.last_collect_date import LastCollectDate


class CollectCorpInfoView(TemplateView):
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'

    try:
        lastest_collect_date = LastCollectDate.objects.last().last_corp_collect_date
    except ProgrammingError:
        lastest_collect_date = None
    except AttributeError:
        LastCollectDate.objects.create()
        lastest_collect_date = LastCollectDate.objects.last().last_corp_collect_date

    context = {
        'last_corp_collect_date': lastest_collect_date
    }   
    
    def get(self, request): # get_corp_info
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_corp()     

        return render(self.request, self.template_name, context=self.context)
    
class CollectStockPriceView(View):
    template_name = 'admin_dashboard/data_collect/collect_stock_price.html'

    try:
        lastest_stock_date = LastCollectDate.objects.last().last_stock_collect_date
    except ProgrammingError:
        lastest_stock_date = None
    except AttributeError:
        LastCollectDate.objects.create()
        lastest_stock_date = LastCollectDate.objects.last().last_stock_collect_date

    context = {
        'last_stock_collect_date': lastest_stock_date,
        'date_logs' : [],
        'corp_logs' : []
    }

    def get(self, request): # get_stock_price
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            fail_corp, fail_date = collect_stock_price()
            self.context['date_logs'] += fail_date
            self.context['corp_logs'] += fail_corp
            
        return render(self.request, self.template_name, context=self.context)

class CollectFinancialStatementView(View):
    template_name = 'admin_dashboard/data_collect/collect_summary_financial_statements.html'

    try:
        lastest_summaryfs_date = LastCollectDate.objects.last().last_summaryfs_collect_date
    except ProgrammingError:
        lastest_summaryfs_date = None
    except AttributeError:
        LastCollectDate.objects.create()
        lastest_summaryfs_date = LastCollectDate.objects.last().last_summaryfs_collect_date

    context = {
        'last_summaryfs_collect_date': lastest_summaryfs_date,
        'logs' : []
    }

    years = [2020, 2021, 2022, 2023]
    quarters = [1, 2, 3, 4]
    def post(self, request):
        if request.method == 'POST':
            year = request.POST.get('year')
            quarter =  request.POST.get('quarter')
            # 입력값 전처리
            choice_year = []
            choice_quarter = []
            if year == 'all':
                choice_year = self.years
            else:
                choice_year.append(int(year))
            if quarter == 'all':
                choice_quarter = self.quarters
            else:
                choice_quarter.append(self.quarters[int(quarter)-1])
            # 수집 실행
            for year in choice_year:
                for quarter in choice_quarter:
                    logs = collect_summary_finaicial_statements(year, quarter)
                    self.context['logs'] += logs
    
        return render(self.request, self.template_name, context=self.context)

    def get(self, request):
        return render(self.request, self.template_name, context=self.context)
