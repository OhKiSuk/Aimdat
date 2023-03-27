"""
@created at 2023.03.22
@author JSU in Aimdat Team
"""

from django.views.generic import DetailView
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from django.contrib.auth.mixins import UserPassesTestMixin
from ..models.corp_id import CorpId
from ..models.corp_info import CorpInfo
from ..models.corp_summary_financial_statements import CorpSummaryFinancialStatements as FS
from ..models.stock_price import StockPrice

class CorpDetailView(UserPassesTestMixin, DetailView):
    model = CorpId
    template_name = 'services/corp_detail_view.html'
    context_object_name = 'corp_id'
    
    def test_func(self):
        user = self.request.user
        date = user.expiration_date if user.is_authenticated else None
        return date and date >= datetime.now()
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse('account:login'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        context['corp_info'] = CorpInfo.objects.get(corp_id=pk)
        context['stock_price'] = StockPrice.objects.filter(corp_id=pk).latest('trade_date')
        context['price_graph_data'] = StockPrice.objects.filter(corp_id=pk).values('trade_date', 'open_price', 'high_price', 'low_price', 'close_price')
        context['trade_graph_data'] = StockPrice.objects.filter(corp_id=pk).values('trade_date', 'trade_quantity')
        context['report_data'] = self.recent_report(pk)
        return context

    #데이터 추출(사업보고서, 분기보고서)
    def recent_report(self, pk):
        y_count = 0
        q_count = 0
        y_data = []
        q_data = []
        
        for y in range(1, 5):
            year = (timezone.now() - timedelta(days=365 * y)).year
            obj = FS.objects.filter(corp_id=pk, year=year, month=12)
            if obj:
                y_data.append(obj)
                y_count += 1
            if y_count == 3:
                break
            if q_count == 3:
                continue
            for q in [12, 9, 6, 3]:
                obj = FS.objects.filter(corp_id=pk, year=year, month=q)
                if obj:
                    q_data.append(obj)
                    q_count += 1
        
        # 최신 값을 뒤로 정렬
        y_data.reverse()
        q_data.reverse()
        
        # 데이터가 3개 미만일 경우 빈 값 삽입
        while True:
            if len(y_data) < 3:
                y_data.append(' ')
                continue
            break
        
        while True:
            if len(q_data) < 3:
                q_data.append(' ')
                continue
            break
        
        data = [y_data, q_data]
        return data
