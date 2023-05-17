"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.05.17
@author OKS in Aimdat Team
"""
from django import forms
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo

class CorpIdChangeForm(forms.ModelForm):
    is_crawl = forms.BooleanField()

    class Meta:
        model = CorpId
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        #label명 정의
        self.fields['corp_name'].label = '기업명'
        self.fields['corp_country'].label = '소속 국가'
        self.fields['corp_market'].label = '소속 시장'
        self.fields['corp_isin'].label = '국제 증권 식별번호(ISIN)'
        self.fields['stock_code'].label = '종목 코드'
        self.fields['corp_sectors'].label = '소속 섹터'
        self.fields['is_crawl'].label = '데이터 자동 수집 여부'

        #각 field class에 form class 추가
        for field_name in self.fields:
            if field_name == 'is_crawl':
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-check-input',
                })
            else:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                })

class CorpInfoChangeForm(forms.ModelForm):

    class Meta:
        model = CorpInfo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['corp_homepage_url'].label = '기업 홈페이지 주소'
        self.fields['corp_settlement_month'].label = '기업 결산월'
        self.fields['corp_ceo_name'].label = 'CEO 이름'
        self.fields['corp_summary'].label = '기업 설명'

        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Textarea):
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'rows': '10',
                })
            else:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                })