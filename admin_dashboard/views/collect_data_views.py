"""
author: cslee

@modified at 2023.05.12
@author OKS in Aimdat Team
"""
from django.contrib import messages
from datetime import datetime
from django.db.utils import ProgrammingError
from django.shortcuts import (
    render, 
    redirect
)
from django.views.generic import (
    TemplateView, 
    View
)
from ..modules.collect.corp import collect_corp
from ..modules.collect.investment_index import save_investment_index
from ..modules.collect.stock_price import collect_stock_price
from ..modules.collect.summary_financial_statements import collect_summary_finaicial_statements
from ..modules.collect.fcorp_financial_statements import save_fcorp
from ..modules.collect.dcorp_financial_statements import save_dcorp

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

class CollectFcorpFinancialStatementsView(View):
    template_name = 'admin_dashboard/data_collect/collect_fcorp_financial_statements.html'

    def post(self, request):
        if request.method == 'POST':
            year = request.POST.get('year')
            quarter = request.POST.get('quarter')
            fs_type = request.POST.get('fs_type')

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
                        result = save_fcorp(y, q, fs)

            # 수집 성공 시 수집일 변경
            if result:
                try:
                    lastest_fs_date = LastCollectDate.objects.last()
                    lastest_fs_date.last_summaryfs_collect_date = datetime.today()
                    lastest_fs_date.save()
                except AttributeError:
                    LastCollectDate.objects.create()
                    lastest_fs_date = LastCollectDate.objects.last()
                    lastest_fs_date.last_summaryfs_collect_date = datetime.today()
                    lastest_fs_date.save()

        return render(self.request, self.template_name, context={'lastest_collect_date': datetime.today()})
    
    def get(self, request):
        try:
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date
        except ProgrammingError:
            lastest_fs_date = None
        except AttributeError:
            LastCollectDate.objects.create()
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date
        
        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})

class CollectDcorpFinancialStatementsView(View):
    """
    비금융기업 재무제표 수집 뷰
    """
    template_name = 'admin_dashboard/data_collect/collect_dcorp_financial_statements.html'

    def post(self, request):
        if request.method == 'POST':
            year = request.POST.get('year')
            quarter = request.POST.get('quarter')

            # 선택하지 않았을 경우 경고 alert
            if year == "none" or quarter == "none":
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
            result = save_dcorp(years, quarters)

            # 수집 성공 시 수집일 변경
            if result:
                try:
                    lastest_fs_date = LastCollectDate.objects.last()
                    lastest_fs_date.last_summaryfs_collect_date = datetime.today()
                    lastest_fs_date.save()
                except AttributeError:
                    LastCollectDate.objects.create()
                    lastest_fs_date = LastCollectDate.objects.last()
                    lastest_fs_date.last_summaryfs_collect_date = datetime.today()
                    lastest_fs_date.save()

        return render(self.request, self.template_name, context={'lastest_collect_date': datetime.today()})

    def get(self, requeset):
        try:
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date
        except ProgrammingError:
            lastest_fs_date = None
        except AttributeError:
            LastCollectDate.objects.create()
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})

class CollectInvestmentIndexView(View):
    """
    투자지표 수집 및 저장 기능
    """
    template_name = 'admin_dashboard/data_collect/collect_investment_index.html'

    def post(self, request):
        year = request.POST.get('year')
        quarter = request.POST.get('quarter')
        fs_type = request.POST.get('fs_type')

        if year == "none" or quarter == "none":
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
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date
        except ProgrammingError:
            lastest_fs_date = None
        except AttributeError:
            LastCollectDate.objects.create()
            lastest_fs_date = LastCollectDate.objects.last().last_summaryfs_collect_date

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})