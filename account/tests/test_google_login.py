"""
@created at 2023.03.08
@author OKS in Aimdat Team
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

from ..models import User

class GoogleLoginTest(TestCase):
    """
    구글 로그인 테스트
    """
    def setUp(self):
        self.client = Client()
        self.google_callback_url = reverse('account:google_login_callback')

    def test_google_login_success(self):
        email = 'test@gmail.com'
        session = self.client.session
        session['state'] = 'test_state'
        session.save()

        with patch('requests.post') as mock_requests_post:
            with patch('requests.get') as mock_requests_get:
                mock_requests_post.return_value.json.return_value = {'access_token': 'test_access_token'}
                mock_requests_get.return_value.json.return_value = {'email': email}

                response = self.client.get(
                    self.google_callback_url,
                    {
                        'state': 'test_state',
                        'code': 'test_code'
                    }
                )

        user = User.objects.get(email=email)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:signup'))
        self.assertEqual(user.email, email)