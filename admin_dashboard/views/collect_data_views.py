"""
author: cslee
"""
from django.shortcuts import render
from django.views.generic import TemplateView, View
from admin_dashboard.models.last_collect_date import LastCollectDate
from admin_dashboard.modules.collect.corp import collect_corp
from admin_dashboard.modules.collect.stock_price import collect_stock_price
from admin_dashboard.modules.collect.summary_finaicial_statements import collect_summary_finaicial_statements


class CollectCorpInfoView(TemplateView):
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'
    context = {
        'last_corp_collect_date' : LastCollectDate.objects.get().last_corp_collect_date,
    }   
    
    def get(self, request): # get_corp_info
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_corp()     

        return render(self.request, self.template_name, context=self.context)
    
class CollectStockPriceView(View):
    template_name = 'admin_dashboard/data_collect/collect_stock_price.html'
    context = {
        'last_stock_collect_date' : LastCollectDate.objects.get().last_stock_collect_date
    }

    def get(self, request): # get_stock_price
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_stock_price()
            
        return render(self.request, self.template_name, context=self.context)

class CollectFinancialStatementView(View):
    template_name = 'admin_dashboard/data_collect/collect_summary_financial_statements.html'
    context = {
        'last_summaryfs_collect_date' : LastCollectDate.objects.get().last_summaryfs_collect_date
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
                    collect_summary_finaicial_statements(year, quarter)
    
        return render(self.request, self.template_name, context=self.context)

    def get(self, request):
        return render(self.request, self.template_name, context=self.context)
