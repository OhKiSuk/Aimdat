"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.04.04
@author OKS in Aimdat Team
"""
from account.views.naver_login_views import NaverCallbackView
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
from unittest.mock import patch

class NaverLoginTest(TestCase):
    """
    네이버 로그인 테스트
    """
    def setUp(self):
        self.client = Client()
        self.naver_callback_url = reverse('account:naver_login_callback')
        self.user_model = get_user_model()

    @patch('requests.post')
    @patch.object(NaverCallbackView, 'get_naver_profile')
    def test_naver_login_success(self, mock_get_naver_profile, mock_post):
        email = 'test@naver.com'
        session = self.client.session
        session['state'] = 'test_state'
        session.save()

        mock_post.return_value.text = '{"access_token": "test_access_token"}'

        mock_profile = {
            'response': {
                'email': email
            }
        }
        mock_get_naver_profile.return_value = mock_profile

        response = self.client.get(
            self.naver_callback_url,
            {
                'state': 'test_state',
                'code': 'test_code'
            }
        )

        user = self.user_model.objects.get(email=email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(user.email, email)

class NaverLoginLinkOffTest(TestCase):

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
        self.user.user_classify = 'N'
        self.user.expiration_date = timezone.now() + timedelta(days=30)
        self.user.refresh_token = 'refresh_token'
        self.user.save()

        self.factory = RequestFactory()
        request = self.factory.get('account:login')
        self.client.login(request=request, username='testuser@aimdat.com', password='testPassword1!')
        
    @patch('requests.post')
    def test_delete_account_success_if_naver_login_user(self, mock_post):
        """
        네이버 소셜 로그인 사용자가 사용자 계정 삭제 시도를 할 경우 성공
        """
        mock_post.return_value.text = '{"result":"success"}'

        response = self.client.get(reverse('account:naver_login_linkoff'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(email='testuser@aimdat.com').exists())

    @patch('requests.post')
    def test_delete_account_failure_if_naver_login_user(self, mock_post):
        """
        네이버 소셜 로그인 사용자의 연동 해제에 실패했을 경우
        """
        mock_post.return_value.text = '{"error":"failure"}'

        response = self.client.get(reverse('account:naver_login_linkoff'))
        self.assertEqual(response.status_code, 500)
        self.assertTrue(get_user_model().objects.filter(email='testuser@aimdat.com').exists())