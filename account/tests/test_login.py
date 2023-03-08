"""
@created at 2023.03.08
@author OKS in Aimdat Team
"""
from django.test import TestCase, Client
from django.test.utils import override_settings

from ..models import User

class ServiceLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()

        User.objects.create_user(
            email='test@aimdat.com',
            password='testpassword1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )

    def tearDown(self):
        User.objects.all().delete()
    
    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_service_login_with_valid_data(self):
        """
        유효한 데이터로 로그인 성공 여부 테스트
        """
        email = 'test@aimdat.com'
        password = 'testpassword1!'

        login_successful = self.client.login(username=email, password=password)

        self.assertTrue(login_successful)