"""
@created at 2023.03.25
@author cslee in Aimdat Team

@modified at 2023.07.19
@author OKS in Aimdat Team
"""

import logging

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
from pathlib import Path

from services.models.corp_id import CorpId
from services.models.investment_index import InvestmentIndex

from ..modules.collect.corp_id import save_corp_id
from ..modules.collect.corp_info import save_corp_info
from ..modules.collect.investment_index import save_investment_index
from ..modules.collect.stock_price import save_stock_price
from ..modules.collect.fcorp_financial_statements import save_fcorp
from ..modules.collect.dcorp_financial_statements import save_dcorp

from ..models.last_collect_date import LastCollectDate

#django 앱 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

LOGGER = logging.getLogger(__name__)

class CollectCorpIdView(TemplateView):
    """
    기업 식별자 정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_corp_id.html'  

    def get(self, request):
        tab = request.GET.get('tab', 'none_action')
        logs = []

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='corp_id').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        if tab == 'collect':
            result = save_corp_id()

            if result:
                LastCollectDate.objects.create(
                    collect_user = request.user.email,
                    collect_type = 'corp_id'
                )
                # A101 로깅
                LOGGER.info('[A101] 기업 식별자 정보를 성공적으로 수집. {}'.format(str(request.user)))
            else:
                # A102 로깅
                LOGGER.error('[A102] 기업 식별자 정보가 정상 수집되지 않음. {}'.format(str(request.user)))

        # 로그 출력        
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A1' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'last_corp_collect_date': lastest_collect_date,
            'logs': logs
        }

        return render(self.request, self.template_name, context=context)

class CollectCorpInfoView(TemplateView):
    """
    기업 정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_corp_info.html'   
    
    def get(self, request):
        tab = request.GET.get('tab', 'none_action')
        logs = []

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='corp_info').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        if tab == 'collect':
            result = save_corp_info()

            if result:
                LastCollectDate.objects.create(
                    collect_user = request.user.email,
                    collect_type = 'corp_info'
                )
                # A201 로깅
                LOGGER.info('[A201] 기업 정보를 성공적으로 수집. {}'.format(str(request.user)))
            else:
                # A202 로깅
                LOGGER.error('[A202] 기업정보가 정상 수집되지 않음. {}'.format(str(request.user)))

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A2' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'last_corp_collect_date': lastest_collect_date,
            'logs': logs
        }

        return render(self.request, self.template_name, context=context)
    
class CollectStockPriceView(View):
    """
    주가정보 수집
    """
    template_name = 'admin_dashboard/data_collect/collect_stock_price.html'

    def get(self, request):
        tab = request.GET.get('tab', 'none_action')
        logs = []
        result = ''

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='stock_price').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        if tab == 'all_collect':
            result = save_stock_price(tab)
        elif tab == 'not_collected':
            result = save_stock_price(tab)
            
        if result:
            LastCollectDate.objects.create(
                collect_user = request.user.email,
                collect_type = 'stock_price'
            )
            # A301 로깅
            LOGGER.info('[A301] 주가 정보를 성공적으로 수집. {}'.format(str(request.user)))
        else:
            # A302 로깅
            LOGGER.error('[A302] 주가 정보가 정상 수집되지 않음. {}'.format(str(request.user)))

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A3' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'lastest_collect_date': lastest_collect_date,
            'logs': logs
        }
            
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
        logs = []

        # 허용된 입력값이 아니면 500에러 리턴
        year = self._verify_data(request.POST.get('year'))
        quarter = self._verify_data(request.POST.get('quarter'))
        fs_type = self._verify_data(request.POST.get('fs_type'))

        # 선택하지 않았을 경우 경고 alert
        if year == "none" or quarter == "none" or fs_type == "none":
            messages.success(self.request, '항목을 선택해주세요.')
            return redirect('admin:collect_fcorp_fs')

        # 최근 3년치 재무제표만 수집 가능(금년 제외)
        if year == 'all':
            now_year = datetime.now().year
            years = [now_year - i for i in range(1, 4, 1)]
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

                    if result:
                        LastCollectDate.objects.create(
                            collect_user = request.user.email,
                            collect_type = 'fcorp_fs'
                        )
                        # A501 로깅
                        LOGGER.info('[A501] 금융 재무제표를 성공적으로 수집. {}, {}, {}, {}'.format(str(request.user), str(year), str(quarter), str(fs_type)))
                    else:
                        # A502 로깅
                        LOGGER.info('[A502] 금융 재무제표가 정상 수집되지 않음. {}, {}, {}, {}'.format(str(request.user), str(year), str(quarter), str(fs_type)))

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='fcorp_fs').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A5' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'lastest_collect_date': lastest_collect_date,
            'logs': logs
        }

        return render(self.request, self.template_name, context=context)
    
    def get(self, request):
        logs = []

        try:
            lastest_collect_date = LastCollectDate.objects.filter(collect_type='fcorp_fs').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_collect_date = '수집 기록이 없습니다.'

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A5' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'lastest_collect_date': lastest_collect_date,
            'logs': logs
        }
        
        return render(self.request, self.template_name, context=context)

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
        logs = []

        # 허용된 입력값이 아니면 500에러 리턴
        year = self._verify_data(request.POST.get('year'))
        quarter = self._verify_data(request.POST.get('quarter'))

        # 선택하지 않았을 경우 경고 alert
        if year == "none" or quarter == "none":
            messages.success(self.request, '항목을 선택해주세요.')
            return redirect('admin:collect_dcorp_fs')

        # 최근 3년치 재무제표만 수집 가능(금년 제외)
        if year == 'all':
            now_year = datetime.now().year
            years = [now_year - i for i in range(1, 4, 1)]
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

        result = save_dcorp(years, quarters)

        if result:
            LastCollectDate.objects.create(
                collect_user = request.user.email,
                collect_type = 'dcorp_fs'
            )
            # A401 로깅
            LOGGER.info('[A401] 비금융 재무제표를 성공적으로 수집. {}, {}, {}'.format(str(request.user), str(year), str(quarter)))
        else:
            # A402 로깅
            LOGGER.error('[A402] 비금융 재무제표가 정상 수집되지 않음. {}, {}, {}'.format(str(request.user), str(year), str(quarter)))

        lastest_collect_date = LastCollectDate.objects.filter(collect_type='dcorp_fs').last()
        if lastest_collect_date:
            lastest_collect_date = lastest_collect_date.collect_date.strftime('%Y-%m-%d')
        else:
            lastest_collect_date = '수집 기록이 없습니다.'

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A4' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'lastest_collect_date': lastest_collect_date,
            'logs': logs
        }

        return render(self.request, self.template_name, context=context)

    def get(self, requeset):
        logs = []

        try:
            lastest_collect_date = LastCollectDate.objects.filter(collect_type='dcorp_fs').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_collect_date = '수집 기록이 없습니다.'

        # 로그 출력
        with open(BASE_DIR / 'aimdat/logs/aimdat_admin_dashboard.log', 'r', encoding='utf-8') as f:
            for line in f:
                if 'A4' in line:
                    split_line = ''.join(line.split('\t')[:2] + line.split('\t')[3:])
                    logs.append(split_line)

        context = {
            'lastest_collect_date': lastest_collect_date,
            'logs': logs
        }

        return render(self.request, self.template_name, context=context)

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
        
        exclude_fields = ['id', 'corp_id', 'year', 'quarter', 'fs_type']
        for y in years:
            for q in quarters:
                for f in fs_types:
                    data_list = save_investment_index(y, q, f)

                    if data_list:
                        InvestmentIndex.objects.bulk_create(
                            data_list, 
                            update_conflicts=True,
                            unique_fields=['id', 'corp_id', 'year', 'quarter', 'fs_type'],
                            update_fields=[f.name for f in InvestmentIndex._meta.fields if f.name not in exclude_fields]
                        )

                        # A601 로깅
                        LOGGER.info('[A601] 투자지표를 성공적으로 수집. {}, {}, {}'.format(str(request.user), str(year), str(quarter)))
                    else:
                        # A602 로깅
                        LOGGER.error('[A602] 투자지표가 정상 수집되지 않음. {}, {}, {}'.format(str(request.user), str(year), str(quarter), fs_type))

        try:
            lastest_fs_date = LastCollectDate.objects.filter(collect_type='investment_index').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_fs_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})
            
    def get(self, request):
        try:
            lastest_fs_date = LastCollectDate.objects.filter(collect_type='investment_index').last().collect_date.strftime('%Y-%m-%d')
        except (ProgrammingError, AttributeError):
            lastest_fs_date = '수집 기록이 없습니다.'

        return render(self.request, self.template_name, context={'lastest_collect_date': lastest_fs_date})