"""
@create at 2023.04.21
@author JSU in Aimdat Team
"""

from django.shortcuts import render
from django.views.generic import TemplateView
from ..modules.collect.ifrs_xbrl import get_ifrs_xbrl_txt, txt_to_json, import_json

class CollectIFRSView(TemplateView):
    template_name = 'admin_dashboard/data_collect/collect_ifrs.html'

    def get(self, requeset):
        get_ifrs_xbrl_txt()
        txt_to_json()
        import_json()

        return render(self.request, self.template_name)
