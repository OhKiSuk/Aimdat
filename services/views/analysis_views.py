"""
@created at 2023.03.28
@author JSU in Aimdat Team

@modified at 2023.06.21
@author OKS in Aimdat Team
"""
import json
import logging

from django.db.models import (
    F, 
    Q
)
from django.http import (
    HttpResponse,
    JsonResponse
)
from django.shortcuts import render

from django.utils import timezone
from django.views.generic import ListView

from ..models.investment_index import InvestmentIndex


LOGGER = logging.getLogger(__name__)

class AnalysisView(ListView):
    model = InvestmentIndex
    template_name = 'services/analysis_view.html'
    
    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False
            if self.request.user.expiration_date.date() >= timezone.now().date():
                return True
            
        return False
    
    def get_queryset(self):
        queryset = super().get_queryset()

        if 'field_list' in self.request.session:
            fields = self.request.session['field_list']
        else:
            fields = ['revenue', 'operating_profit', 'operating_margin', 'dividend', 'dividend_ratio']
        
        # 분석 기업 선택 시
        if 'analysis_list' in self.request.session:
            q = Q()
            for obj in self.request.session['analysis_list']:
                
                for key, values in obj.items():
                    q |= Q(corp_id__exact=key, year__exact=values['year'], quarter__exact=values['quarter'], fs_type__exact=values['fs_type'])
            
            queryset = queryset.filter(q).values('corp_id__corp_name', 'corp_id', 'year', 'quarter', 'fs_type', *fields)
            return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 지표 구분
        account_index = ['revenue', 'operating_profit', 'net_profit', 'cost_of_sales']
        investment_index = [
            'cost_of_sales_ratio',
            'operating_margin',
            'net_profit_margin',
            'roe',
            'roa',
            'current_ratio',
            'quick_ratio',
            'debt_ratio',
            'per',
            'pbr',
            'psr',
            'eps',
            'bps',
            'ev_ebitda',
            'ev_ocf',
        ]
        dividend_index = ['dividend', 'dividend_ratio', 'dividend_payout_ratio', 'dps']

        context['account_index'] = account_index
        context['investment_index'] = investment_index
        context['dividend_index'] = dividend_index
        
        if 'analysis_list' in self.request.session:
            context['analysis_list'] = self.request.session['analysis_list']

        if 'field_list' in self.request.session:
            context['field_list'] = self.request.session['field_list']
        else:
            context['field_list'] = ['revenue', 'operating_profit', 'operating_margin', 'dividend', 'dividend_ratio']
            
        return context
    
    def post(self, request):

        # 검색 기록 초기화
        if 'reset' in request.body.decode('utf-8'):

            remove_session_keys = ['analysis_list', 'field_list']
            session_keys = request.session.keys()
            for key in remove_session_keys:
                if key in session_keys:
                    del self.request.session[key]

        # 분석할 기업정보를 분석 페이지에서 추가했을 경우
        elif request.POST.get('selected_corp'):
            if not self.test_func():
                return HttpResponse('로그인이 필요한 서비스입니다.', status=500)

            selected_corp = json.loads(request.POST.get('selected_corp'))
            if 'stock_code' not in selected_corp:
                return HttpResponse('기업을 선택해주세요.', status=500)

            stock_code = selected_corp['stock_code']
            year = selected_corp['year']
            quarter = selected_corp['quarter']
            fs_type = selected_corp['fs_type']

            if len(stock_code) == 6 and str(stock_code).isdecimal():
                q = Q(corp_id__stock_code__exact=stock_code) & Q(year__exact=year) & Q(quarter__exact=quarter) & Q(fs_type__exact=fs_type)
            else:
                return HttpResponse('존재하지 않는 기업입니다.', status=500)
            
            try:
                result = InvestmentIndex.objects.get(q)
            except InvestmentIndex.DoesNotExist:
                return HttpResponse('존재하지 않는 기업입니다.', status=500)

            if 'analysis_list' in request.session:
                analysis_list = request.session['analysis_list']

                # 기업 정보가 중첩되는 지 확인
                appended_list = []
                for items in analysis_list:
                    for key in items.keys():
                        appended_list.append(int(key))

                for items in request.session['analysis_list']:

                    for key, values in items.items():
                        q |= Q(corp_id__exact=key, year__exact=values['year'], quarter__exact=values['quarter'], fs_type__exact=values['fs_type'])
                        if key == result.corp_id.id:
                            if values['year'] != year and values['quarter'] != year and values['quarter'] != fs_type:
                                analysis_list.append({result.corp_id.id: {
                                    'year': year, 
                                    'quarter': quarter, 
                                    'fs_type': fs_type
                                }})
                                appended_list.append(result.corp_id.id)
                        else:
                            if result.corp_id.id not in appended_list:
                                analysis_list.append({result.corp_id.id: {
                                    'year': year, 
                                    'quarter': quarter, 
                                    'fs_type': fs_type
                                }})
                                appended_list.append(result.corp_id.id)
            else:
                analysis_list = [{result.corp_id.id: {'year': year, 'quarter': quarter, 'fs_type': fs_type}}]

            request.session['analysis_list'] = analysis_list
            # U302 로깅
            LOGGER.info('[U302] 분석 시도한 기업 정보. {}'.format(analysis_list))

            if 'field_list' in self.request.session:
                fields = self.request.session['field_list']
                # U301 로깅
                LOGGER.info('[U301] 분석 시도한 필터 정보. {}'.format(fields))
            else:
                fields = ['revenue', 'operating_profit', 'operating_margin', 'dividend', 'dividend_ratio']

            return JsonResponse({
                'object_list': list(self.get_queryset().values('corp_id', 'year', 'quarter', 'fs_type', *fields, corp_name=F('corp_id__corp_name'))),
                'field_list': fields
            }, safe=False)

        # 지표 설정
        elif request.POST.get('field_list'):
            if not self.test_func():
                return HttpResponse('로그인이 필요한 서비스입니다.', status=500)

            field_list = json.loads(request.POST.get('field_list'))

            if field_list:
                self.request.session['field_list'] = field_list
            else:
                self.request.session['field_list'] = ['revenue', 'operating_profit', 'operating_margin', 'dividend', 'dividend_ratio']
            
            fields = self.request.session['field_list']
            # U301 로깅
            LOGGER.info('[U301] 분석 시도한 필터 정보. {}'.format(fields))

            return JsonResponse({
                'object_list': list(self.get_queryset().values('corp_id', 'year', 'quarter', 'fs_type', *fields, corp_name=F('corp_id__corp_name'))),
                'field_list': fields
            }, safe=False)

        elif request.POST.get('checked_corp'):
            # 검색 페이지에서 비교할 기업을 선택하여 기업 분석 버튼을 클릭했을 경우
            if 'analysis_list' in request.session:
                analysis_list = request.session['analysis_list']
                
                appended_list = []
                for corp in request.POST.getlist('checked_corp'):
                    corp_info = corp.split(',')
                    corp_id = int(corp_info[0])
                    year = corp_info[1]
                    quarter = corp_info[2]
                    fs_type = corp_info[3]
                    
                    # 기업 정보가 중첩되는 지 확인
                    for items in analysis_list:
                        for key in items.keys():
                            appended_list.append(int(key))

                    for items in request.session['analysis_list']:
                        for key, values in items.items():
                            if key == corp_id:
                                if values['year'] != year and values['quarter'] != year and values['quarter'] != fs_type:
                                    analysis_list.append({corp_id: {
                                        'year': year, 
                                        'quarter': quarter, 
                                        'fs_type': fs_type
                                    }})
                                    appended_list.append(corp_id)
                            else:
                                if corp_id not in appended_list:
                                    analysis_list.append({corp_id: {
                                        'year': year, 
                                        'quarter': quarter, 
                                        'fs_type': fs_type
                                    }})
                                    appended_list.append(corp_id)

                request.session['analysis_list'] = analysis_list
                # U302 로깅
                LOGGER.info('[U302] 분석 시도한 기업 정보. {}'.format(analysis_list))

            else:
                corp_info_list = []
                for corp in request.POST.getlist('checked_corp'):
                    corp_info = corp.split(',')
                    corp_id = corp_info[0]
                    year = corp_info[1]
                    quarter = corp_info[2]
                    fs_type = corp_info[3]

                    corp_info_dict = {corp_id: {'year': year, 'quarter': quarter, 'fs_type': fs_type}}
                    corp_info_list.append(corp_info_dict)

                request.session['analysis_list'] = corp_info_list
                # U302 로깅
                LOGGER.info('[U302] 분석 시도한 기업 정보. {}'.format(corp_info_list))

        self.object_list = self.get_queryset()
        context = self.get_context_data()

        return render(request, 'services/analysis_view.html', context=context)
    
    def get(self, request):

        if request.GET.get('corp_info'):
            corp_info = json.loads(request.GET.get('corp_info'))
            corp_name = corp_info['corp_name']
            year = corp_info['year']
            quarter = corp_info['quarter']
            fs_type = corp_info['fs_type']

            # 종목코드 검색 및 종목명 입력 구분
            if len(corp_name) == 6 and str(corp_name).isdecimal():
                q = Q(corp_id__stock_code__icontains=corp_name) & Q(year__exact=year) & Q(quarter__exact=quarter) & Q(fs_type__exact=fs_type)
            else:
                q = Q(corp_id__corp_name__icontains=corp_name) & Q(year__exact=year) & Q(quarter__exact=quarter) & Q(fs_type__exact=fs_type)

            # 기업 검색 결과
            result = InvestmentIndex.objects.filter(q).order_by('-corp_id_id').\
                values(corp_name=F('corp_id__corp_name'), stock_code=F('corp_id__stock_code'), corp_sectors=F('corp_id__corp_sectors'), corp_country=F('corp_id__corp_country'), corp_market=F('corp_id__corp_market'))

            if result:
                return JsonResponse(list(result), safe=False)
            else:
                return HttpResponse('검색 결과가 존재하지 않습니다.', status=500)

        self.object_list = self.get_queryset()
        context = self.get_context_data()

        return render(request, self.template_name, context=context)