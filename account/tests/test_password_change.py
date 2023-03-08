"""
@created at 2023.03.08
@author OKS in Aimdat Team
"""
from django.http import HttpRequest
from django.test import TestCase, Client
from django.urls import reverse

from ..models import User

class CustomPasswordChangeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@aimdat.com',
            password='testuser1!',
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )

    def tearDown(self):
        User.objects.all().delete()

    def test_password_change_success(self):
        """
        사용자가 정상적으로 비밀번호 변경에 성공하는 경우
        """
        email = 'test@aimdat.com'
        password = 'testuser1!'
        self.client.login(request=HttpRequest(), username=email, password=password)

        response = self.client.put(reverse('account:password_change'), {
            'old_password': self.user.password,
            'new_password1': 'newpassword',
            'newpassword2': 'newpassword'
        })

        self.assertEqual(response.status_code, 200)

    def test_password_change_failure_with_wrong_old_password_(self):
        """
        사용자가 잘못된 기존 비밀번호를 입력하여 실패하는 경우
        """
        email = 'test@aimdat.com'
        password = 'testuser1!'
        self.client.login(request=HttpRequest(), username=email, password=password)

        response = self.client.put(reverse('account:password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword',
            'newpassword2': 'newpassword'
        })

        self.assertEqual(response.status_code, 200)