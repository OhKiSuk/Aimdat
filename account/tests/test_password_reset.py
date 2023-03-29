"""
@created at 2023.03.08
@author OKS in Aimdat Team

@modified at 2023.03.28
@author OKS in Aimdat Team
"""
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase, Client
from django.urls import reverse
from ..models import User

class CustomPasswordResetViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testuser1!',
            is_not_teen=True,
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_dispatch_if_login(self):
        """
        로그인한 사용자가 패스워드 재설정 메일 전송 페이지로 접근할 경우
        """
        email = 'test@aimdat.com'
        password = 'testuser1!'
        self.client.login(request=HttpRequest(), username=email, password=password)

        response = self.client.get(reverse('account:password_reset'))
        
        self.assertEqual(response.status_code, 302)

    def test_if_email_valid(self):
        """
        패스워드 재설정을 위해 사용자가 이메일을 입력한 경우
        """
        email = 'test@aimdat.com'

        response = self.client.post(reverse('account:password_reset'), {'email': email})
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(response.status_code, 302)

    def test_if_email_invaild(self):
        """
        패스워드 재설정을 위해 사용자가 작성한 이메일이 존재하지 않는 경우
        """
        email = 'testfail@aimdat.com'

        response = self.client.post(reverse('account:password_reset'), {'email': email})

        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(response.status_code, 200)

class CustomPasswordConfirmViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testuser1!',
            is_not_teen=True,
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )
        self.response = self.client.post(reverse('account:password_reset'), {'email': self.user.email})

        self.email_url = mail.outbox[0].body

    def tearDown(self):
        User.objects.all().delete()

    def test_if_confirm_password_success(self):
        """
        사용자가 올바른 새 비밀번호를 입력해 비밀번호 재설정에 성공했을 경우
        """
        response = self.client.post(self.email_url, {'new_password1': 'newpassword', 'new_password2': 'newpassword'})

        self.assertEqual(response.status_code, 302)