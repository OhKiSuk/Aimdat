"""
@created at 2023.03.20
@author JSU in Aimdat Team

@modified at 2023.03.26
@author JSU in Aimdat Team
"""

from django.test import TestCase
from datetime import datetime, timedelta
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.http import QueryDict
from decimal import Decimal
from account.models import User
from ..models.corp_summary_financial_statements import CorpSummaryFinancialStatements as fs
from ..models.corp_id import CorpId

class SearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testpassword1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )
        cls.factory = RequestFactory()
        corp_1 = CorpId.objects.create(corp_name = '삼성')
        corp_2 = CorpId.objects.create(corp_name = '엘지')
        corp_3 = CorpId.objects.create(corp_name = '한화')
        
        fs.objects.create(
            disclosure_date = '2022-12-12',
            year = '2022',
            month = '12',
            revenue = Decimal('1'),
            net_profit = Decimal('-10'),
            corp_id = corp_1)
        fs.objects.create(
            disclosure_date = '2022-12-12',
            year = '2022',
            month = '12',
            revenue = Decimal('100'),
            net_profit = Decimal('30'),
            corp_id = corp_2)
        fs.objects.create(
            disclosure_date = '2022-12-12',
            year = '2022',
            month = '12',
            revenue = Decimal('100'),
            net_profit = Decimal('30'),
            corp_id = corp_3)
        
    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_expired_access(self):
        """
        서비스 이용 만료 접근 테스트
        """
        email = 'test@aimdat.com'
        password = 'testpassword1!'

        self.user.expiration_date = datetime.now() - timedelta(days=1)
        request = self.factory.get(reverse('services:detail', kwargs={'pk': self.corp.pk}))
        expired_login = self.client.login(request=request, username=email, password=password)
        self.assertTrue(expired_login)
        response = self.client.get(reverse('services:detail', kwargs={'pk': self.corp.pk}))
        self.assertEqual(response.status_code, 302)

    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_normal_access(self):
        """
        서비스 이용자 접근 허용 테스트
        """
        email = 'test@aimdat.com'
        password = 'testpassword1!'

        self.user.expiration_date = datetime.now() + timedelta(days=1)

        request = self.factory.get(reverse('services:detail', kwargs={'pk': self.corp.pk}))
        normal_login = self.client.login(request=request, username=email, password=password)
        self.assertTrue(normal_login)
        
    def test_selection_of_condition(self):
        """
        사용자가 조건을 지정한 경우
        """
        data = QueryDict('name_en=revenue&name_ko=매출액&revenue_min=1&revenue_max=50')
        response = self.client.post(reverse('services:search'), data=data)
        self.assertEqual(response.status_code, 200)
        
        self.assertQuerysetEqual(
            response.context['object_list'], 
            ['<CorpSummaryFinancialStatements: CorpSummaryFinancialStatements object (1)>'],
            ordered=False,
            transform=repr
        )

    def test_refresh_after_condition_selection(self):
        """
        사용자가 조건을 지정한 후 새로고침을 한 경우
        """
        session = self.client.session
        session['name_en'] = ['revenue']
        session['name_ko'] = ['매출액']
        session['min'] = ['1']
        session['max'] = ['50']
        session.save()

        response = self.client.get(reverse('services:search'))
        self.assertEqual(response.status_code, 200)
    
        self.assertQuerysetEqual(
            response.context['object_list'], 
            ['<CorpSummaryFinancialStatements: CorpSummaryFinancialStatements object (1)>'],
            ordered=False,
            transform=repr
        )
    
    def test_multiple_selection_of_conditions(self):
        """
        여러 개의 조건을 지정한 경우
        """
        data = QueryDict('name_en=revenue&name_ko=매출액&revenue_min=1&revenue_max=200&'
            'name_en=net_profit&name_ko=순이익&net_profit_min=-20&net_profit_max=20')
        response = self.client.post(reverse('services:search'), data=data)
        self.assertEqual(response.status_code, 200)
        
        self.assertQuerysetEqual(
            response.context['object_list'], 
            ['<CorpSummaryFinancialStatements: CorpSummaryFinancialStatements object (1)>'],
            ordered=False,
            transform=repr
        )
