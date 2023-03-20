"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.19
@author OKS in Aimdat Team
"""
from account.views.naver_login_views import NaverCallbackView
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
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