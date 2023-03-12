"""
@created at 2023.03.12
@author OKS in Aimdat Team
"""
from account.models import User
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

class AccountManageAdminTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            email='testadmin@aimdat.com',
            password='testadmin1!'
        )
        self.factory = RequestFactory()
    
    def tearDown(self):
        User.objects.all().delete()
    
    def test_add_superuser_success(self):
        """
        관리자 계정 생성이 성공적으로 완료되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        response = self.client.post(reverse('admin:account_user_add'), {'email': 'testadmin2@aidmat.com', 'password1': 'testadmin1!', 'password2': 'testadmin1!'})

        self.assertTrue(response.status_code, 302)

    def test_change_superuser_success(self):
        """
        관리자 계정 정보 변경이 성공적으로 완료되는지 테스트
        """
        User.objects.create_superuser(
            email='testadmin2@aimdat.com',
            password='testadmin1!'
        )

        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        user_id = User.objects.get(email='testadmin2@aimdat.com')

        response = self.client.post(reverse('admin:account_user_change', args=[user_id.id]), {'email': 'testchange@aimdat.com', 'password': 'testadmin1!'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.get(email='testchange@aimdat.com').id, user_id.id)

    def test_delete_superuser_success(self):
        """
        관리자 계정 정보 삭제가 성공적으로 완료되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        user_id = User.objects.get(email=email)

        response = self.client.post(reverse('admin:account_user_delete', args=[user_id.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(email='testadmin@aimdat.com').exists())