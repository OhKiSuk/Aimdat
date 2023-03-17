"""
@created at 2023.03.17
@author OKS in Aimdat Team
"""
from django.shortcuts import render
from django.views.generic import TemplateView

class MarketingView(TemplateView):
    
    def get(self, request, *args, **kwargs):
        tab = request.GET.get('tab', 'user')

        context = {
            'tab': tab
        }

        return render(request, 'admin_dashboard/marketing/marketing.html', context=context)