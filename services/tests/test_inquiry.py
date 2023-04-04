"""
@created at 2023.04.04
@author OKS in Aimdat Team
"""
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

from ..models.inquiry import Inquiry

class AddInquiryViewTest(TestCase):

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
        self.user.expiration_date = timezone.now() + timedelta(days=30)
        self.user.save()
        self.factory = RequestFactory()
        
        request = self.factory.get(reverse('account:login'))
        self.client.login(request=request, username='testuser@aimdat.com', password='testPassword1!')

    def tearDown(self) -> None:
        get_user_model().objects.all().delete()
        
    def test_add_inquiry_success_with_vaild_data(self):
        """
        사용자가 정상적인 데이터를 삽입해서 1:1 문의 작성에 성공한 경우
        """
        data = {
            'title': 'testtitle',
            'inquiry_category': 'account',
            'content': 'testcontent'
        }

        response = self.client.post(reverse('services:add_inquiry'), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Inquiry.objects.filter(title='testtitle').exists())

    def test_add_inquiry_failure_with_invalid_category(self):
        """
        사용자가 의도하지 않은 category를 삽입해서 1:1 문의 작성을 시도하는 경우 실패
        """
        data = {
            'title': 'testtitle',
            'inquiry_category': 'wrongcategory',
            'content': 'testcontent'
        }

        response = self.client.post(reverse('services:add_inquiry'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Inquiry.objects.filter(title='testtitle').exists())
        self.assertContains(response, '잘못된 입력입니다.')

    def test_add_inquiry_failure_category_not_choice(self):
        """
        사용자가 category를 선택하지 않고 1:1 문의 작성을 시도하는 경우 실패
        """
        data = {
            'title': 'testtitle',
            'inquiry_category': 'choices',
            'content': 'testcontent'
        }
        response = self.client.post(reverse('services:add_inquiry'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Inquiry.objects.filter(title='testtitle').exists())
        self.assertContains(response, '문의유형을 선택하세요.')