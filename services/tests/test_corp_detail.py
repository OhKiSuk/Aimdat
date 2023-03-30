"""
@created at 2023.03.24
@author JSU in Aimdat Team
"""

from datetime import timedelta

from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from account.models import User

from ..models.corp_id import CorpId


class DetailTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testpassword1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )
        self.factory = RequestFactory()
        self.corp = CorpId.objects.create(corp_name = '삼성')
        
    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def test_expired_access(self):
        """
        서비스 이용 만료 접근 테스트
        """
        email = 'test@aimdat.com'
        password = 'testpassword1!'

        self.user.expiration_date = timezone.now() - timedelta(days=1)
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

        self.user.expiration_date = timezone.now() + timedelta(days=1)

        request = self.factory.get(reverse('services:detail', kwargs={'pk': self.corp.pk}))
        normal_login = self.client.login(request=request, username=email, password=password)
        self.assertTrue(normal_login)
