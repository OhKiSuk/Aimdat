"""
author: cslee
"""
from django.shortcuts import render
from django.views.generic import TemplateView
from admin_dashboard.modules.collect.corp import collect_corp

class CollectCorpInfoView(TemplateView):
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'

    def get(self, request): # get_corp_info
        tab = request.GET.get('tab', 'none_action')
        if tab == 'collect':
            collect_corp()

        return render(self.request, self.template_name)
    