"""
@created at 2023.03.22
@author JSU in Aimdat Team

@modified at 2023.04.07
@author JSU in Aimdat Team
"""

from datetime import timedelta

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import DetailView

from ..models.corp_id import CorpId
from ..models.corp_info import CorpInfo
from ..models.corp_summary_financial_statements import \
    CorpSummaryFinancialStatements as FS
from ..models.stock_price import StockPrice


class CorpDetailView(UserPassesTestMixin, DetailView):
    model = CorpId
    template_name = 'services/corp_detail_view.html'
    context_object_name = 'corp_id'
    pk_url_kwarg = 'id'
    
    def test_func(self):
        auth = self.request.user.is_authenticated
        if auth:
            date = self.request.user.expiration_date.date() >= timezone.now().date()
            return auth and date
        return False
    
    def handle_no_permission(self):
        return redirect('account:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        id = self.kwargs.get(self.pk_url_kwarg)
        context['corp_info'] = CorpInfo.objects.get(corp_id=id)
        context['stock_price'] = StockPrice.objects.filter(corp_id=id).latest('trade_date')
        context['price_graph_data'] = StockPrice.objects.filter(corp_id=id).values('trade_date', 'open_price', 'high_price', 'low_price', 'close_price')
        context['trade_graph_data'] = StockPrice.objects.filter(corp_id=id).values('trade_date', 'trade_quantity')
        context['report_data'] = self.recent_report(id)
        return context

    #데이터 추출(사업보고서, 분기보고서)
    def recent_report(self, id):
        y_data = []
        q_data = []
        
        for y in range(1, 5):
            if len(y_data) == 3:
                break
            year = (timezone.now() - timedelta(days=365 * y)).year
            obj = FS.objects.filter(corp_id=id, year=year, month=12)
            if obj:
                y_data.append(obj)

            for q in [12, 9, 6, 3]:
                if len(q_data) == 3:
                    break
                obj = FS.objects.filter(corp_id=id, year=year, month=q)
                if obj:
                    q_data.append(obj)
        
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
