"""
@created at 2023.04.04
@author OKS in Aimdat Team
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import (
    Client,
    RequestFactory,
    TestCase
)
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

class DeleteAccountTest(TestCase):
    """
    사용자 계정 삭제 테스트
    """

    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            email='testuser@aimdat.com',
            password='testPassword1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True,
            is_not_teen=True
        )
        self.user.expiration_date = timezone.now() + timedelta(days=30)
        self.user.save()

        request = self.factory.get(reverse('account:login'))
        self.client.login(request=request, username='testuser@aimdat.com', password='testPassword1!')

    def tearDown(self) -> None:
        get_user_model().objects.all().delete()

    def test_delete_account_success_if_default_user(self):
        """
        사용자가 일반 사용자(Aimdat을 통해 회원가입한 경우)일 때 사용자 계정 삭제 성공 테스트
        """
        response = self.client.post(reverse('account:delete_account'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(email='testuser@aimdat.com').exists())