"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.19
@author OKS in Aimdat Team
"""
from datetime import timedelta
from django.test import (
    Client,
    RequestFactory,
    TestCase
)
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from ..models import User
from ..views.kakao_login_views import KakaoLinkOffView

class KakaoLoginTest(TestCase):
    """
    카카오 로그인 테스트
    """
    def setUp(self):
        self.client = Client()
        self.kakao_callback_url = reverse('account:kakao_login_callback')

    def test_kakao_login_success(self):
        email = 'test@kakao.com'
        session = self.client.session
        session['state'] = 'test_state'
        session.save()

        with patch('requests.post') as mock_requests_post:
            with patch('requests.get') as mock_requests_get:
                mock_requests_post.return_value.json.return_value = {'access_token': 'test_access_token'}
                mock_requests_get.return_value.json.return_value = {'kakao_account': {'email': email}}

                response = self.client.get(
                    self.kakao_callback_url,
                    {
                        'state': 'test_state',
                        'code': 'test_code'
                    }
                )

        user = User.objects.get(email=email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.email, email)

class KakaoLoginLinkOffTest(TestCase):

    @override_settings(AUTHENTICATION_BACKENDS=['account.backends.EmailBackend'])
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@aimdat.com',
            password='testPassword1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True,
            is_not_teen=True
        )
        self.user.user_classify = 'K'
        self.user.expiration_date = timezone.now() + timedelta(days=30)
        self.user.refresh_token = 'refresh_token'
        self.user.save()

        self.factory = RequestFactory()
        request = self.factory.get('account:login')
        self.client.login(request=request, username='testuser@aimdat.com', password='testPassword1!')
        
    @patch('requests.post')
    @patch.object(KakaoLinkOffView, 'linkoff')
    def test_delete_account_success_if_kakao_login_user(self, mock_linkoff, mock_post):
        """
        카카오 소셜 로그인 사용자가 사용자 계정 삭제 시도를 할 경우 성공
        """
        mock_post.return_value.text = '{"access_token": "test_token"}'
        mock_linkoff.return_value = {"id": "12345"}

        response = self.client.get(reverse('account:kakao_login_linkoff'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(email='testuser@aimdat.com').exists())

    @patch('requests.post')
    @patch.object(KakaoLinkOffView, 'linkoff')
    def test_delete_account_failure_if_kakao_login_user(self, mock_linkoff, mock_post):
        """
        카카오 소셜 로그인 사용자의 연동 해제에 실패했을 경우
        """
        mock_post.return_value.text = '{"access_token": "test_token"}'
        mock_linkoff.return_value = None

        response = self.client.get(reverse('account:kakao_login_linkoff'))
        self.assertEqual(response.status_code, 500)
        self.assertTrue(User.objects.filter(email='testuser@aimdat.com').exists())