"""
@created at 2023.08.11
@author OKS in Aimdat Team
"""
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'services/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 지표 구분
        account_index = [
            'revenue', 
            'operating_profit', 
            'net_profit',
            'total_assets',
            'total_debt',
            'total_capital',
            'operating_cash_flow',
            'investing_cash_flow',
            'financing_cash_flow',
        ]
        safety_index = [
            'current_ratio',
            'quick_ratio',
            'debt_ratio',
            'interest_coverage_ratio'
        ]
        profitability_index = [
            'cost_of_sales_ratio',
            'gross_profit_margin',
            'operating_margin',
            'net_profit_margin',
            'roic',
            'roe',
            'roa'
        ]
        activity_index = [
            'total_assets_turnover',
            'inventory_turnover',
            'accounts_receivables_turnover',
            'accounts_payable_turnover',
            'working_capital_requirement',
            'working_capital_once'
        ]
        growth_index = [
            'revenue_growth',
            'operating_profit_growth',
            'net_profit_growth',
            'net_worth_growth',
            'assets_growth'
        ]
        investment_index = [
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
        context['safety_index'] = safety_index
        context['profitability_index'] = profitability_index
        context['activity_index'] = activity_index
        context['growth_index'] = growth_index
        context['investment_index'] = investment_index
        context['dividend_index'] = dividend_index

        return context