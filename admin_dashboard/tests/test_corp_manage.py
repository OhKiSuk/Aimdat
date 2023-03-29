"""
@created at 2023.03.16
@author OKS in Aimdat Team

@modified at 2023.03.24
@author OKS in Aidmat Team
"""
from account.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements

class CorpManageTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            email='testadmin@aimdat.com',
            password='testadmin1!'
        )
        self.factory = RequestFactory()
        self.corp_id = CorpId.objects.create(
            corp_name = 'test',
            corp_country = 'test',
            corp_market = 'test',
            corp_isin = 'test',
            stock_code = 'test',
            corp_sectors = 'test',
            is_crawl = False
        )
        self.corp_info = CorpInfo.objects.create(
            corp_id = self.corp_id,
            corp_homepage_url = 'http://www.test.com',
            corp_settlement_month = '2000-12-31',
            corp_ceo_name = 'test',
            corp_summary = 'test',
        )
        self.corp_summary = CorpSummaryFinancialStatements.objects.create(
            corp_id = self.corp_id,
            disclosure_date = '2000-12-31',
            year = '9999',
            month = '12',
            revenue = 00.00,
            operating_profit = 00.00,
            net_profit = 00.00,
            operating_margin = 00.00,
            net_profit_margin = 00.00,
            debt_ratio = 00.00,
            cost_of_sales_ratio = 00.00,
            quick_ratio = 00.00,
            dividend = 00.00,
            total_dividend = 00.00,
            dividend_yield = 00.00,
            dividend_payout_ratio = 00.00,
            dividend_ratio = 00.00,
            per = 00.00,
            pbr = 00.00,
            psr = 00.00,
            ev_ebitda = 00.00,
            ev_per_ebitda = 00.00,
            eps = 00.00,
            bps = 00.00,
            roe = 00.00,
            dps = 00.00,
            total_debt = 00.00,
            total_asset = 00.00,
            total_capital = 00.00,
            borrow_debt = 00.00,
            face_value = 00.00,
        )
    
    def tearDown(self):
        User.objects.all().delete()
        CorpId.objects.all().delete()
        CorpInfo.objects.all().delete()
        CorpSummaryFinancialStatements.objects.all().delete()
    
    def test_change_corp_id_success(self):
        """
        기업 리스트가 정상적으로 변경되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:corp_id_change', args=[self.corp_id.id]), {'corp_name': 'testcorp'})

        self.assertTrue(response.status_code, 302)

    def test_change_corp_id_success(self):
        """
        기업 정보가 정상적으로 변경되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:corp_info_change', args=[self.corp_info.corp_id.id]), {'corp_summary': 'testinfo'})

        self.assertTrue(response.status_code, 302)

    def test_change_corp_id_success(self):
        """
        기업 요약재무제표가 정상적으로 변경되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:corp_summary_change', args=[self.corp_summary.corp_id.id]), {'revenue': '10.00'})

        self.assertTrue(response.status_code, 302)