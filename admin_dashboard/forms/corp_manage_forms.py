"""
@created at 2023.03.15
@author OKS in Aimdat Team

@modified at 2023.03.20
@author OKS in Aimdat Team
"""
from django import forms
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements

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
        self.fields['corp_settlement_date'].label = '기업 결산일'
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

class CorpSummaryFinancialStatementsChangeForm(forms.ModelForm):

    class Meta:
        model = CorpSummaryFinancialStatements
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['disclosure_date'].label = '공시일'
        self.fields['year'].label = '년도'
        self.fields['month'].label = '월'
        self.fields['revenue'].label = '매출액'
        self.fields['operating_profit'].label = '영업이익'
        self.fields['net_profit'].label = '당기순이익'
        self.fields['operating_margin'].label = '영업이익률'
        self.fields['net_profit_margin'].label = '순이익률'
        self.fields['debt_ratio'].label = '부채비율'
        self.fields['cost_of_sales_ratio'].label = '매출원가율'
        self.fields['quick_ratio'].label = '당좌비율'
        self.fields['dividend'].label = '배당금'
        self.fields['total_dividend'].label = '총 배당금'
        self.fields['dividend_yield'].label = '배당 수익률'
        self.fields['dividend_payout_ratio'].label = '배당성향'
        self.fields['dividend_ratio'].label = '배당률'
        self.fields['per'].label = 'PER'
        self.fields['pbr'].label = 'PBR'
        self.fields['psr'].label = 'PSR'
        self.fields['ev_ebitda'].label = 'EV/EVITDA'
        self.fields['ev_per_ebitda'].label = 'EV/PER_EBITDA'
        self.fields['eps'].label = 'EPS'
        self.fields['bps'].label = 'BPS'
        self.fields['roe'].label = 'ROE'
        self.fields['dps'].label = 'DPS'
        self.fields['total_debt'].label = '총 부채'
        self.fields['total_asset'].label = '총 자산'
        self.fields['total_capital'].label = '총 자본'
        self.fields['borrow_debt'].label = '총 차입금'
        self.fields['face_value'].label = '액면가'

        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control'
            })