"""
author: cslee
"""
from django.shortcuts import render
from django.views.generic import TemplateView, View
from admin_dashboard.modules.collect.corp import collect_corp
from admin_dashboard.modules.collect.stock import collect_stockPrice

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
            print(1)
            collect_stockPrice()
            
        return render(self.request, self.template_name)