"""
@created at 2023.03.08
@author OKS in Aimdat Team
"""
import re

from account.views.naver_login_views import NaverCallbackView
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse
from unittest.mock import patch

from ..models import User

class SendPinViewTest(TestCase):

    def test_send_pin_success(self):
        """
        PIN 번호를 생성 후 이메일 전송 성공 여부 테스트
        """
        response = self.client.post(reverse('account:send_pin'), {'email': 'test@aimdat.com'})

        self.assertEqual(response.status_code, 302)
        self.assertIn('pin', self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Aimdat] 회원가입 PIN 번호 발송 안내')
        self.assertEqual(self.client.session.get_expiry_age(), 1800)

class SignUpViewTest(TestCase):
    
    def test_signup_with_valid_data(self):
        """
        유효한 데이터로 회원가입 성공 여부 테스트
        """
        self.client = Client()
        self.user_data = {
            'email': 'test@aimdat.com',
            'password1': 'testpassword1!',
            'password2': 'testpassword1!',
            'terms_of_use_agree': True,
            'terms_of_privacy_agree': True,
        }

        self.client.post(reverse('account:send_pin'), data={'email': 'test@aimdat.com'})
        match = re.search(r'\d{6}', mail.outbox[0].body)
        pin = match.group()

        self.user_data['pin'] = pin

        response = self.client.post(reverse('account:signup'), data=self.user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account:signup'))

        #회원가입 성공 여부 확인
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

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
        self.assertRedirects(response, reverse('account:signup'))
        self.assertEqual(user.email, email)

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
        self.assertRedirects(response, reverse('account:signup'))
        self.assertEqual(user.email, email)