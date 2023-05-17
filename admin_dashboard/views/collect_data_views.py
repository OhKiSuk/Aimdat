"""
@created at 2023.03.25
@author cslee in Aimdat Team

@modified at 2023.05.17
@author OKS in Aimdat Team
"""
from django.contrib import messages
from datetime import datetime
from django.db.utils import ProgrammingError
from django.http import HttpResponseServerError
from django.shortcuts import (
    render, 
    redirect
)
from django.views.generic import (
    TemplateView, 
    View
)
from ..modules.collect.corp_id import save_corp_id
from ..modules.collect.corp_info import save_corp_info
from ..modules.collect.investment_index import save_investment_index
from ..modules.collect.stock_price import save_stock_price
from ..modules.collect.fcorp_financial_statements import save_fcorp
from ..modules.collect.dcorp_financial_statements import save_dcorp

from ..models.last_collect_date import LastCollectDate

class CollectCorpIdView(TemplateView):
    """
    기업 식별자 정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_corp_id.html'  

    def get(self, request):
        tab = request.GET.get('tab', 'none_action')

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='corp_id').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        context = {
            'last_corp_collect_date': lastest_collect_date,
            'fail_logs': []
        }

        if tab == 'collect':
            logs, result = save_corp_id()
            context['fail_logs'] += logs

            if result:
                LastCollectDate.objects.create(
                    collect_user = request.user.email,
                    collect_type = 'corp_id'
                )

        return render(self.request, self.template_name, context=context)

class CollectCorpInfoView(TemplateView):
    """
    기업 정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'   
    
    def get(self, request):
        tab = request.GET.get('tab', 'none_action')

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='corp_info').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        context = {
            'last_corp_collect_date': lastest_collect_date,
            'fail_logs': []
        }

        if tab == 'collect':
            logs, result = save_corp_info()
            context['fail_logs'] += logs

            if result:
                LastCollectDate.objects.create(
                    collect_user = request.user.email,
                    collect_type = 'corp_info'
                )

        return render(self.request, self.template_name, context=context)
    
class CollectStockPriceView(View):
    """
    주가정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_stock_price.html'

    def get(self, request):
        tab = request.GET.get('tab', 'none_action')

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='stock_price').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        context = {
            'lastest_collect_date': lastest_collect_date,
            'fail_logs' : []
        }

        if tab == 'collect':
            fail_logs, result = save_stock_price()
            context['fail_logs'] += fail_logs
            
            if result:
                LastCollectDate.objects.create(
                    collect_user = request.user.email,
                    collect_type = 'stock_price'
                )
            
        return render(self.request, self.template_name, context=context)

class CollectFcorpFinancialStatementsView(View):
    """
    금융기업 재무제표 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_fcorp_financial_statements.html'

    def _verify_data(self, data):
        """
        입력 값 검증 함수
        """
        if data in ['none', 'all'] or str(data).isdecimal():
            return data

        return HttpResponseServerError

    def post(self, request):
        # 허용된 입력값이 아니면 500에러 리턴
        year = self._verify_data(request.POST.get('year'))
        quarter = self._verify_data(request.POST.get('quarter'))
        fs_type = self._verify_data(request.POST.get('fs_type'))

        # 선택하지 않았을 경우 경고 alert
        if year == "none" or quarter == "none" or fs_type == "none":
            messages.success(self.request, '항목을 선택해주세요.')
            return redirect('admin:collect_fcorp_fs')

        # 최근 5년치 재무제표만 수집 가능
        if year == 'all':
            now_year = datetime.now().year
            years = [now_year - i for i in range(5)]
        else:
            years = [int(year)]

        # 분기 {1: 1분기, 2: 반기, 3: 3분기, 4: 사업보고서}
        if quarter == 'all':
            quarters = [1, 2, 3, 4]
        else:
            quarters = [int(quarter)]

        # 재무제표 종류 {0: 연결재무제표, 5: 일반재무제표}
        if fs_type == "all":
            fs_types = [0, 5]
        else:
            fs_types = [int(fs_type)]

        # 재무제표 수집
        for y in years:
            for q in quarters:
                for fs in fs_types:
                    logs, result = save_fcorp(y, q, fs)

        # 수집 성공 시 수집 로그 저장
        if result:
            LastCollectDate.objects.create(
                collect_user = request.user.email,
                collect_type = 'fcorp_fs'
            )

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='fcorp_fs').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_collect_date, 'logs': logs})
    
    def get(self, request):
        try:
            lastest_collect_date = LastCollectDate.objects.filter(collect_type='fcorp_fs').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_collect_date = '수집 기록이 없습니다.'
        
        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_collect_date})

class CollectDcorpFinancialStatementsView(View):
    """
    비금융기업 재무제표 수집 뷰
    """
    template_name = 'admin_dashboard/data_collect/collect_dcorp_financial_statements.html'

    def _verify_data(self, data):
        """
        입력 값 검증 함수
        """
        if data in ['none', 'all'] or str(data).isdecimal():
            return data

        return HttpResponseServerError

    def post(self, request):
        # 허용된 입력값이 아니면 500에러 리턴
        year = self._verify_data(request.POST.get('year'))
        quarter = self._verify_data(request.POST.get('quarter'))

        # 선택하지 않았을 경우 경고 alert
        if year == "none" or quarter == "none":
            messages.success(self.request, '항목을 선택해주세요.')
            return redirect('admin:collect_dcorp_fs')

        # 최근 5년치 재무제표만 수집 가능
        if year == 'all':
            now_year = datetime.now().year
            years = [now_year - i for i in range(5)]
        else:
            years = [int(year)]

        # 분기 {1: 1분기, 2: 반기, 3: 3분기, 4: 사업보고서}
        if quarter == 'all':
            quarters = ['1분기', '반기', '3분기', '사업']
        elif quarter == '1':
            quarters = ['1분기']
        elif quarter == '2':
            quarters = ['반기']
        elif quarter == '3':
            quarters = ['3분기']
        elif quarter == '4':
            quarters = ['사업']

        # 재무제표 수집
        logs, result = save_dcorp(years, quarters)

        # 수집 성공 시 수집 로그 저장
        if result:
            LastCollectDate.objects.create(
                collect_user = request.user.email,
                collect_type = 'dcorp_fs'
            )

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='dcorp_fs').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_collect_date, 'logs': logs})

    def get(self, requeset):
        try:
            lastest_collect_date = LastCollectDate.objects.filter(collect_type='dcorp_fs').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_collect_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_collect_date})

class CollectInvestmentIndexView(View):
    """
    투자지표 수집 및 저장 기능
    """
    template_name = 'admin_dashboard/data_collect/collect_investment_index.html'

    def _verify_data(self, data):
        """
        입력 값 검증 함수
        """
        if data in ['none', 'all'] or str(data).isdecimal():
            return data

        return HttpResponseServerError

    def post(self, request):
        year = self._verify_data(request.POST.get('year'))
        quarter = self._verify_data(request.POST.get('quarter'))
        fs_type = self._verify_data(request.POST.get('fs_type'))

        if year == "none" or quarter == "none" or fs_type == "none":
            messages.success(self.request, '항목을 선택해주세요.')
            return redirect('admin:collect_fcorp_fs')
        
        # 최근 5년치 재무제표만 수집 가능
        if year == 'all':
            now_year = datetime.now().year
            years = [now_year - i for i in range(5)]
        else:
            years = [int(year)]

        # 분기 {1: 1분기, 2: 반기, 3: 3분기, 4: 사업보고서}
        if quarter == 'all':
            quarters = [1, 2, 3, 4]
        else:
            quarters = [int(quarter)]

        # 재무제표 종류 {0: 연결재무제표, 5: 별도재무제표}
        if fs_type == "all":
            fs_types = ['0', '5']
        else:
            fs_types = [fs_type]

        for y in years:
            for q in quarters:
                for f in fs_types:
                    save_investment_index(y, q, f)

        return render(self.request, self.template_name)
    
    def get(self, request):
        try:
            lastest_fs_date = LastCollectDate.objects.filter(collect_type='investment_index').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_fs_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})