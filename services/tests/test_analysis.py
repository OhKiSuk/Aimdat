"""
@created at 2023.04.13
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


class AnalysisTest(TestCase):
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

            CorpId.objects.create(id=99999, corp_name='testcorp')
            FS.objects.create(disclosure_date=timezone.now(), corp_id_id=99999, revenue=10, operating_profit=20, operating_margin=30, net_profit=40, dividend=50, dividend_ratio=60, total_debt=10)

    def test_access_failure_with_expired_account(self):
        """
        서비스 이용 만료자 접근 실패 테스트
        """
        self.user.expiration_date = timezone.now() - timezone.timedelta(days=1)
        self.user.save()

        request = self.factory.get(reverse('services:analysis'))
        self.client.login(request=request)
        response = self.client.get(reverse('services:analysis'))
        self.assertEqual(response.status_code, 302)

    def test_access_success_with_normal_account(self):
        """
        서비스 이용자 접근 성공 테스트
        """
        response = self.client.get(reverse('services:analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testcorp')        

    def test_success_with_default_data(self):
        """
        기업만 설정된 요청 성공 테스트
        """
        response = self.client.post(reverse('services:analysis'), data={'checked_corp': '99999, 2022, 3'})
        self.assertEqual(response.context['analysis_data'], ['revenue', 'operating_profit', 'operating_margin', 'net_profit', 'dividend', 'dividend_ratio'])