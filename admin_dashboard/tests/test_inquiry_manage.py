"""
@created at 2023.03.13
@author OKS in Aimdat Team
"""
from account.models import User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from services.models.inquiry import Inquiry

from ..models.inquiry_answer import InquiryAnswer

class InquiryManageTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@aidmat.com',
            password='testUser1!',
            is_not_teen=True,
            terms_of_use_agree=True,
            terms_of_privacy_agree=True
        )

        self.admin = User.objects.create_superuser(
            email='testadmin@aimdat.com',
            password='testadmin1!'
        )

        self.factory = RequestFactory()
        self.inquiry = Inquiry.objects.create(
            user = self.user,
            title='test',
            inquiry_category='test',
            content='test'
        )
    
    def tearDown(self):
        User.objects.all().delete()
        Inquiry.objects.all().delete()
        InquiryAnswer.objects.all().delete()
    
    def test_add_inquiry_answer_success(self):
        """
        답변이 정상적으로 작성되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:add_inquiry_answer', args=[self.inquiry.id]), {'content': 'test answer'})

        self.assertTrue(response.status_code, 302)
        self.assertTrue(InquiryAnswer.objects.filter(inquiry_id=self.inquiry.id).exists())