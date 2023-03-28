"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.28
@author OKS in Aimdat Team
"""
import re
from django.core import mail
from django.test import Client, RequestFactory, TestCase 
from django.urls import reverse
from ..models import User

class SendPinViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        User.objects.all().delete()

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

    def test_is_authenticated_user_access_fail(self):
        """
        로그인한 사용자가 접근할 경우 접근에 실패하는 것을 확인하는 테스트
        """
        User.objects.create_user(
            email='testsendpin@aimdat.com',
            password='testsendpin1!',
            is_not_teen=True,
            terms_of_privacy_agree=True,
            terms_of_use_agree=True
        )
        factory = RequestFactory()

        request = factory.get(reverse('account:login'))
        self.client.login(request=request, username='testsendpin@aimdat.com', password='testsendpin1!')

        response = self.client.post(reverse('account:send_pin'), {'email': 'abcdef@absfda.com'})
        self.assertEqual(response.status_code, 403)

class SignUpViewTest(TestCase):

    def setUp(self):
        self.clinet = Client()
        self.user_data = {
            'email': 'testfailure@aimdat.com',
            'password1': 'testpassword1!',
            'password2': 'testpassword1!',
            'is_not_teen': True,
            'terms_of_use_agree': True,
            'terms_of_privacy_agree': True
        }

    def tearDown(self):
        User.objects.all().delete()
    
    def test_signup_with_valid_data(self):
        """
        유효한 데이터로 회원가입 성공 여부 테스트
        """
        user_data = {
            'email': 'testsuccess@aimdat.com',
            'password1': 'testpassword1!',
            'password2': 'testpassword1!',
            'is_not_teen': True,
            'terms_of_use_agree': True,
            'terms_of_privacy_agree': True,
        }

        self.client.post(reverse('account:send_pin'), data={'email': 'test@aimdat.com'})
        match = re.search(r'\d{6}', mail.outbox[0].body)
        pin = match.group()

        user_data['pin'] = pin

        response = self.client.post(reverse('account:signup'), data=user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('account:signup'))
        self.assertTrue(User.objects.filter(email=user_data['email']).exists())

    def test_signup_with_pin_if_not_number(self):
        """
        핀 번호를 숫자가 아닌 문자로 잘못 입력했을 경우
        """
        self.user_data['pin'] = 'notpin'
        response = self.client.post(reverse('account:signup'), data=self.user_data, follow=True)
        self.assertContains(response, "PIN번호가 올바르지 않습니다.")

    def test_signup_with_pin_if_mismatch_length(self):
        """
        핀 번호를 숫자로 입력했으나 길이가 다른 경우
        """
        self.user_data['pin'] = '1234567'
        response = self.client.post(reverse('account:signup'), data=self.user_data, follow=True)
        self.assertContains(response, "이 값이 최대 6 개의 글자인지 확인하세요")