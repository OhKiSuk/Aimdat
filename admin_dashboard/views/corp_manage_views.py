"""
@created at 2023.03.19
@author OKS in Aimdat Team

@modified at 2023.05.25
@author JSU in Aimdat Team
"""

import logging
import pymongo

from bson.decimal128 import Decimal128
from bson.objectid import ObjectId
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import (
    render, 
    redirect
)
from django.urls import reverse_lazy
from django.views.generic import (
    View,
    UpdateView, 
    TemplateView
)

from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from ..forms.corp_manage_forms import (
    CorpIdChangeForm, 
    CorpInfoChangeForm
)

LOGGER = logging.getLogger(__name__)
    
class ManageCorpIdListView(TemplateView):
    """
    기업 식별 목록 뷰
    """
    template_name = 'admin_dashboard/corp_manage/manage_corp_id_list.html'

    def get(self, request):
        content = CorpId.objects.all().order_by('-corp_name')

        page = request.GET.get('page', 1)
        paginator = Paginator(content, 20)
        page_obj = paginator.get_page(page)

        return render(self.request, self.template_name, context={'content': page_obj})
    
class ManageCorpIdUpdateView(UpdateView):
    """
    기업 식별 데이터 갱신
    """
    model = CorpId
    template_name = 'admin_dashboard/corp_manage/manage_corp_id_update.html'
    form_class = CorpIdChangeForm
    success_url = reverse_lazy('admin:manage_corp_id_list')

    def form_valid(self, form):
        if not self.request.user.is_admin:
            # A711 로깅
            LOGGER.info('[A711] 기업 식별자 수정 실패. {}, {}'.format(str(self.request.user), str(form)))
            raise PermissionDenied()
        else:
            # A710 로깅
            LOGGER.info('[A710] 기업 식별자를 성공적으로 수정. {}, {}'.format(str(self.request.user), str(form)))
            form.save()
            return redirect('admin:manage_corp_id_list')
        
class ManageCorpInfoListView(TemplateView):
    """
    기업 정보 목록 뷰
    """
    template_name = 'admin_dashboard/corp_manage/manage_corp_info_list.html'

    def get(self, request):
        content = CorpInfo.objects.all().order_by('-corp_id__corp_name')

        page = request.GET.get('page', 1)
        paginator = Paginator(content, 20)
        page_obj = paginator.get_page(page)

        return render(self.request, self.template_name, context={'content': page_obj})
    
class ManageCorpInfoUpdateView(UpdateView):
    model = CorpInfo
    template_name = 'admin_dashboard/corp_manage/manage_corp_info_update.html'
    form_class = CorpInfoChangeForm
    success_url = reverse_lazy('admin:manage_corp_info_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['corp_name'] = self.object.corp_id.corp_name
        return context

    def form_valid(self, form):
        if not self.request.user.is_admin:
            # A721 로깅
            LOGGER.info('[A721] 기업 정보 수정 실패. {}, {}'.format(str(self.request.user), str(form)))
            raise PermissionDenied()
        else:
            # A720 로깅
            LOGGER.info('[A720] 기업 정보를 성공적으로 수정. {}, {}'.format(str(self.request.user), str(form)))
            form.save()
            return redirect('admin:manage_corp_info_list')

class ManageCorpFinancialStatementsSearchView(View):
    """
    재무제표 검색 뷰
    """
    template_name = 'admin_dashboard/corp_manage/manage_corp_fs_search.html'

    def get(self, reqeust):
        return render(self.request, self.template_name)

    def post(self, request):
        corp_name = request.POST.get('corp_name')
        year = request.POST.get('year')
        quarter = request.POST.get('quarter')
        fs_type = request.POST.get('fs_type')
        fs_name = request.POST.get('fs_name')

        if not corp_name or year == "none" or quarter == "none" or fs_type == "none" or fs_name == "none":
            return redirect('admin:manage_corp_fs_search')
        
        client = pymongo.MongoClient('localhost:27017')
        db = client['aimdat']
        collection = db['financial_statements']

        # 재무제표종류 정의
        if fs_name == "1":
            if fs_type == '0':
                fs_name = "연결재무상태표"
            else:
                fs_name = "별도재무상태표"
        elif fs_name == "2":
            if fs_type == '0':
                fs_name = "연결포괄손익계산서"
            else:
                fs_name = '별도포괄손익계산서'
        elif fs_name == "3":
            if fs_type == '0':
                fs_name = '연결현금흐름표'
            else:
                fs_name = '별도현금흐름표'

        # 기업명으로 검색 시 종목코드로 변환
        if corp_name.isdigit():
            stock_code = corp_name
        else:
            stock_code = CorpId.objects.filter(corp_name=corp_name).values_list('stock_code', flat=True)[0]

        # 재무제표 검색
        query = {'종목코드': stock_code, '년도': int(year), '분기': int(quarter), '재무제표종류': fs_name}
        projection = {'종목코드': 0, '년도': 0, '분기': 0, '재무제표종류': 0}
        result = collection.find_one(query, projection)
        
        search_corp_name = CorpId.objects.filter(stock_code=stock_code).values_list('corp_name', flat=True)[0]

        context = {
            'search_query': [f'기업명: {search_corp_name}({stock_code})', f'{year}년', f'{quarter}분기', fs_name],
            'fs_id': result['_id'],
            'content': result
        }
        
        return render(self.request, self.template_name, context=context)
    
class ManageCorpFinancialStatementsUpdateView(View):
    """
    재무제표 계정과목 수정 뷰
    """

    def post(self, request):
        fs_id = request.POST.get('fs_id')
        key = request.POST.get('key')
        value = request.POST.get('value')

        client = pymongo.MongoClient('localhost:27017')
        db = client['aimdat']
        collection = db['financial_statements']

        # 변경하는 값의 타입 확인(숫자 외에는 str로 저장)
        if value.isdigit():
            result = collection.update_one({'_id': ObjectId(fs_id)}, {'$set': {str(key): Decimal128(str(value))}})
        else:
            result = collection.update_one({'_id': ObjectId(fs_id)}, {'$set': {str(key): str(value)}})

        if result.matched_count == 1:
            # A703 로깅
            LOGGER.info('[A703] 기업 계정과목을 성공적으로 수정. {}, {}, {}, {}'.format(str(request.user)), str(fs_id), str(key), str(value))
            message = {'message': '데이터 수정이 완료되었습니다. 새로고침하여 확인해주세요.'}
        else:
            # A704 로깅
            LOGGER.info('[A704] 기업 계정과목 수정 실패. {}, {}, {}, {}'.format(str(request.user)), str(fs_id), str(key), str(value))
            message = {'message': '데이터 수정에 실패했습니다.'}

        return JsonResponse(message)
    
class ManageCorpFinancialStatementsDeleteView(View):
    """
    재무제표 계정과목 삭제 뷰
    """

    def post(self, request):
        fs_id = request.POST.get('fs_id')
        key = request.POST.get('key')

        client = pymongo.MongoClient('localhost:27017')
        db = client['aimdat']
        collection = db['financial_statements']

        result = collection.update_one({'_id': ObjectId(fs_id)}, {'$unset': {str(key): ''}})

        if result.matched_count == 1:
            # A701 로깅
            LOGGER.info('[A701] 기업 계정과목을 성공적으로 삭제. {}, {}, {}'.format(str(request.user), str(fs_id), str(key)))
            message = {'message': '데이터 삭제가 완료되었습니다. 새로고침하여 확인해주세요.'}
        else:
            # A702 로깅
            LOGGER.info('[A702] 기업 계정과목 삭제 실패. {}, {}, {}'.format(str(request.user), str(fs_id), str(key)))
            message = {'message': '데이터 삭제에 실패했습니다.'}

        return JsonResponse(message)
    
class ManageCorpFinancialStatementsAddView(View):
    """
    재무제표 계정과목 추가 뷰
    """

    def post(self, request):
        fs_id = request.POST.get('fs_id')
        key = request.POST.get('key')
        value = request.POST.get('value')

        client = pymongo.MongoClient('localhost:27017')
        db = client['aimdat']
        collection = db['financial_statements']

        # 필드명 Unique 여부 확인
        check_field = collection.find_one({'$and': [{'_id': ObjectId(fs_id), str(key): {'$exists': True}}]})        

        if check_field:
            return JsonResponse({'message': '이미 존재하는 필드명입니다.'})
        else:
            if value.isdigit():
                result = collection.update_one({"_id": ObjectId(fs_id)}, {"$set": {str(key): Decimal128(str(value))}})
            else:
                result = collection.update_one({"_id": ObjectId(fs_id)}, {"$set": {str(key): value}})

            if result.matched_count == 1:
                # A705 로깅
                LOGGER.info('[A705] 기업 계정과목을 성공적으로 추가. {}, {}, {}, {}'.format(str(request.user)), str(fs_id), str(key), str(value))
                message = {'message': '계정과목 추가가 완료되었습니다. 새로고침하여 확인해주세요.'}
            else:
                # A706 로깅
                LOGGER.info('[A706] 기업 계정과목 추가 실패. {}, {}, {}, {}'.format(str(request.user)), str(fs_id), str(key), str(value))
                message = {'message': '계정과목 추가에 실패했습니다.'}
            
            return JsonResponse(message)