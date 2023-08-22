"""
@created at 2023.08.12
@authro OKS in Aimdat Team
"""
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DeleteView
)

from services.models.corp_id import CorpId
from services.models.reits_inquiry import ReitsInquiry

# 상장리츠 목록
REITS_LIST = [
    '140910',
    '145270',
    '204210',
    '330590',
    '293940',
    '088260',
    '417310',
    '377190',
    '357250',
    '348950',
    '357120',
    '357430',
    '396690',
    '404990',
    '350520',
    '334890',
    '365550',
    '400760',
    '338100',
    '395400',
    '432320',
    '451800',
    '448730'
]

class ReitsManageHome(ListView):
    """
    리츠 관리 페이지
    """
    template_name='admin_dashboard/reits/reits_manage_home.html'
    model = ReitsInquiry
    ordering = ['corp_id__corp_name']

class ReitsAddView(CreateView):
    """
    리츠 정보 추가
    """
    template_name='admin_dashboard/reits/reits_add_view.html'
    model = ReitsInquiry
    fields = ['corp_id', 'establishment_date', 'listing_date', 'settlement_cycle', 'investment_assets_info', 'borrowed_info']
    success_url = reverse_lazy('admin:manage_reits_home')

    def get_form(self):
        form = super().get_form()

        # field label 이름 설정
        form.fields['corp_id'].label = '기업 선택'
        form.fields['establishment_date'].label = '설립일(Y-m-d)'
        form.fields['listing_date'].label = '상장일(Y-m-d)'
        form.fields['settlement_cycle'].label = '결산월'
        form.fields['investment_assets_info'].label = '투자자산 정보'
        form.fields['borrowed_info'].label = '차입금 정보'

        form.fields['corp_id'].queryset = CorpId.objects.filter(stock_code__in=REITS_LIST)

        return form

class ReitsUpdateView(UpdateView):
    """
    리츠 정보 수정
    """
    template_name='admin_dashboard/reits/reits_update_view.html'
    model = ReitsInquiry
    fields = ['corp_id', 'establishment_date', 'listing_date', 'settlement_cycle', 'investment_assets_info', 'borrowed_info']
    success_url = reverse_lazy('admin:manage_reits_home')

    def get_form(self):
        form = super().get_form()

        # field label 이름 설정
        form.fields['corp_id'].label = '기업 선택'
        form.fields['establishment_date'].label = '설립일(Y-m-d)'
        form.fields['listing_date'].label = '상장일(Y-m-d)'
        form.fields['settlement_cycle'].label = '결산월'
        form.fields['investment_assets_info'].label = '투자자산 정보'
        form.fields['borrowed_info'].label = '차입금 정보'
        form.fields['lastest_dividend_date'].label = '최근 배당일'
        form.fields['lastest_dividend_rate'].label = '배당률'

        form.fields['corp_id'].queryset = CorpId.objects.filter(stock_code__in=REITS_LIST)

        return form

class ReitsDeleteView(DeleteView):
    """
    리츠 정보 삭제
    """
    model = ReitsInquiry

    def get_success_url(self):
        return reverse_lazy('admin:manage_reits_home')
    
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)