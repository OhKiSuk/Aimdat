"""
@created at 2023.03.15
@author OKS in Aimdat Team
"""
from django import forms
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements

class CorpIdChangeForm(forms.ModelForm):

    class Meta:
        model = CorpId
        fields = '__all__'

class CorpInfoChangeForm(forms.ModelForm):

    class Meta:
        model = CorpInfo
        fields = '__all__'

class CorpSummaryFinancialStatementsChangeForm(forms.ModelForm):

    class Meta:
        model = CorpSummaryFinancialStatements
        fields = '__all__'