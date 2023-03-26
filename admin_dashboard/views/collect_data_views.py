"""
author: cslee
"""
from django.shortcuts import render
from django.views.generic import TemplateView, View
from admin_dashboard.modules.collect.corp import collect_corp
from admin_dashboard.modules.collect.stock import collect_stockPrice
from admin_dashboard.modules.collect.summaryFS import collect_fs_data

class CollectCorpInfoView(TemplateView):
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'

    def get(self, request): # get_corp_info
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_corp()

        return render(self.request, self.template_name)
    
class CollectStockPriceView(View):
    template_name = 'admin_dashboard/data_collect/collect_stock_price.html'

    def get(self, request): # get_stock_price
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_stockPrice()
            
        return render(self.request, self.template_name)

class CollectFinancialStatementView(View):
    template_name = 'admin_dashboard/data_collect/collect_summary_financial_statements.html'

    years = [2020, 2021, 2022, 2023]
    quarters = [3, 6, 9, 12]
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
            for i in choice_year:
                for j in choice_quarter:
                    collect_fs_data(i, j)
    
        return render(self.request, self.template_name)

    def get(self, request):
        return render(self.request, self.template_name)