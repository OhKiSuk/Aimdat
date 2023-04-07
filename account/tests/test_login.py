"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.04.07
@author OKS in Aimdat Team
"""
from axes.models import AccessAttempt
from datetime import (
    datetime, 
    timedelta
)
from django.test import (
    Client, 
    RequestFactory, 
    TestCase
)
from django.test.utils import override_settings
from django.urls import reverse

from ..models import User

class ServiceLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testpassword1!',
            is_not_teen=True,
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )
        self.factory = RequestFactory()

    def tearDown(self):
        User.objects.all().delete()
        AccessAttempt.objects.all().delete()
    
    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_service_login_with_valid_data(self):
        """
        유효한 데이터로 로그인 성공 여부 테스트
        """
        email = 'test@aimdat.com'
        password = 'testpassword1!'

        self.user.expiration_date = datetime.now() + timedelta(days=1)

        request = self.factory.get(reverse('account:login'))
        login_successful = self.client.login(request=request, username=email, password=password)
        self.assertTrue(login_successful)

    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_service_login_with_invalid_data(self):
        """
        유효하지 않은 데이터로 로그인 시도할 경우 실패 확인 테스트
        """
        email = 'testfailure@aimdat.com'
        password = 'testpassword1!'

        request = self.factory.get(reverse('account:login'))
        login_failure = self.client.login(request=request, username=email, password=password)
        self.assertFalse(login_failure)

    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_service_login_failure_more_than_five_times(self):
        """
        로그인이 5회 이상 연속으로 실패했을 경우 계정이 잠기는지 확인 테스트
        """
        email = 'test@aimdat.com'
        password = 'wrongpassword'

        request = self.factory.get(reverse('account:login'))

        for _ in range(0, 5):
            self.client.login(request=request, username=email, password=password)

        login_failure = self.client.login(request=request, username=email, password=password)
        self.assertFalse(login_failure)
        self.assertTrue(AccessAttempt.objects.filter(username='test@aimdat.com', failures_since_start=6).exists())