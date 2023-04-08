"""
@created at 2023.03.20
@author JSU in Aimdat Team

@modified at 2023.03.26
@author JSU in Aimdat Team

@modified at 2023.03.31
@author JSU in Aimdat Team

@modified at 2023.04.05
@author JSU in Aimdat Team
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from services.models.corp_id import CorpId
from services.models.corp_summary_financial_statements import \
    CorpSummaryFinancialStatements as FS


class SearchTest(TestCase):
    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def setUp(self):
            self.client = Client()
            self.user = get_user_model().objects.create_user(
                email='testuser@aimdat.com',
                password='testPassword1!',
                terms_of_use_agree=True,
                terms_of_privacy_agree=True,
                is_not_teen=True
            )
            self.user.expiration_date = timezone.now()
            self.user.save()
            self.factory = RequestFactory()
            
            request = self.factory.get(reverse('account:login'))
            self.client.login(request=request, username='testuser@aimdat.com', password='testPassword1!')

            for i in range(1, 4):
                CorpId.objects.create(corp_name=f'testcorp{i}')

            for i in range(1, 4):
                FS.objects.create(
                    corp_id = CorpId.objects.get(corp_name=f'testcorp{i}'),
                    disclosure_date = timezone.now(),
                    year = '2022',
                    month = '12',
                    revenue = Decimal(i),
                    net_profit = Decimal(i)
                )
        
    def test_access_failure_with_expired_account(self):
        """
        서비스 이용 만료자 접근 실패 테스트
        """
        self.user.expiration_date = timezone.now() - timezone.timedelta(days=1)
        self.user.save()

        request = self.factory.get(reverse('services:search'))
        self.client.login(request=request)
        response = self.client.get(reverse('services:search'))
        self.assertEqual(response.status_code, 302)

    def test_access_success_with_normal_account(self):
        """
        서비스 이용자 접근 성공 테스트
        """
        response = self.client.get(reverse('services:search'))
        self.assertEqual(response.status_code, 200)

    def test_search_success_with_valid_data(self):
        """
        정상 검색 요청 성공 테스트
        """
        data = {'name_en':'revenue', 'name_ko':'매출액', 'revenue_min':'1', 'revenue_max':'2'}
        response = self.client.post(reverse('services:search'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testcorp1')

    def test_search_failure_with_invalid_data(self):
        """
        비정상 검색 요청 성공 테스트
        """
        data = {'name_en':'revenue', 'name_ko':'매출액', 'revenue_min':'1', 'revenue_max':'2', 'corp':"' OR user='1' --"}
        response = self.client.post(reverse('services:search'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '검색된 데이터가 없습니다.')
