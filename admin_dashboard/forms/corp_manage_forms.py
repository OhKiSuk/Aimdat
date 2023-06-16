"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.06.16
@author OKS in Aimdat Team
"""
from django import forms
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.investment_index import InvestmentIndex

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
        self.fields['base_date'].label = '기준일'

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

class InvestmentIndexChangeForm(forms.ModelForm):

    class Meta:
        model = InvestmentIndex
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            #각 field class에 form class 추가
            if field_name == 'year' or field_name == 'quarter' or field_name == 'fs_type':
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'readonly': 'readonly',
                })
            else:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                })

            # 라벨명 한국어로 변환
            if field_name != 'id' and field_name != 'corp_id':
                self.fields[field_name].label = self.convert_label(field_name)


    def convert_label(self, field_name):
        """
        영문 필드명을 한국어로 변환
        """

        field_name_list = {
            'year':'년도',
            'quarter': '분기',
            'fs_type': '재무제표 유형',
            'revenue': '매출액',
            'operating_profit': '영업이익',
            'net_profit': '당기순이익',
            'cost_of_sales': '매출원가',
            'cost_of_sales_ratio': '매출원가율',
            'operating_margin': '영업이익률',
            'net_profit_margin': '순이익률',
            'roe': 'ROE',
            'roa': 'ROA',
            'current_ratio': '유동비율',
            'quick_ratio': '당좌비율',
            'debt_ratio': '부채비율',
            'per': 'PER',
            'pbr': 'PBR',
            'psr': 'PSR',
            'eps': 'EPS',
            'bps': 'BPS',
            'ev_ebitda': 'EV/EBITDA',
            'ev_ocf': 'EV/OCF',
            'dividend': '배당금',
            'dividend_ratio': '배당률',
            'dividend_payout_ratio': '배당성향',
            'dps': 'DPS'
        }

        return field_name_list[field_name]