"""
@created at 2023.03.08
@author OKS in Aimdat Team
"""
import re

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

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