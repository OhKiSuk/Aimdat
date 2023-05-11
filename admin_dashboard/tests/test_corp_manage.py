"""
@created at 2023.03.16
@author OKS in Aimdat Team

@modified at 2023.05.11
@author OKS in Aidmat Team
"""
from account.models import User
from bson.objectid import ObjectId
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from unittest import mock

class CorpManageTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            email='testadmin@aimdat.com',
            password='testadmin1!'
        )
        self.factory = RequestFactory()
        self.corp_id = CorpId.objects.create(
            corp_name = 'test',
            corp_country = 'test',
            corp_market = 'test',
            corp_isin = 'test',
            stock_code = 'test',
            corp_sectors = 'test',
            is_crawl = False
        )
        self.corp_info = CorpInfo.objects.create(
            corp_id = self.corp_id,
            corp_homepage_url = 'http://www.test.com',
            corp_settlement_month = '2000-12-31',
            corp_ceo_name = 'test',
            corp_summary = 'test',
        )
    
    def tearDown(self):
        User.objects.all().delete()
        CorpId.objects.all().delete()
        CorpInfo.objects.all().delete()
    
    def test_change_corp_id_success(self):
        """
        기업 리스트가 정상적으로 변경되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:manage_corp_id_update', args=[self.corp_id.id]), {'corp_name': 'testcorp'})

        self.assertTrue(response.status_code, 302)

    def test_change_corp_info_success(self):
        """
        기업 정보가 정상적으로 변경되는지 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        response = self.client.post(reverse('admin:manage_corp_info_update', args=[self.corp_info.corp_id.id]), {'corp_summary': 'testinfo'})

        self.assertTrue(response.status_code, 302)

    @mock.patch('pymongo.collection.Collection.find_one')
    def test_corp_fs_search_success(self, mock_find_one):
        """
        기업 재무제표 검색 성공 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)
        
        data = {
            '종목코드': '000000', 
            '년도': 2020, 
            '분기': 1, 
            '재무제표종류': '별도재무상태표'
        }
        
        mock_find_one.return_value = {
            '종목코드': '000000', 
            '년도': 2020, 
            '분기': 1, 
            '재무제표종류': '별도재무상태표',
            'test': '1'
        }
        
        response = self.client.post(reverse('admin:manage_corp_fs_search'), data=data)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual('1', mock_find_one.return_value['test'])

    @mock.patch('pymongo.collection.Collection.update_one')
    def test_corp_fs_update_success(self, mock_update_one):
        """
        기업 재무제표 계정과목 수정 성공 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        data = {
            'fs_id': ObjectId(),
            'key': 'test',
            'value': '1234'
        }

        mock_update_one.return_value = mock.Mock(matched_count=1)
        
        response = self.client.post(reverse('admin:manage_corp_fs_update'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, mock_update_one.return_value.matched_count)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'message': '데이터 수정이 완료되었습니다. 새로고침하여 확인해주세요.'})

    @mock.patch('pymongo.collection.Collection.update_one')
    def test_corp_fs_delete_success(self, mock_update_one):
        """
        기업 재무제표 계정과목 삭제 성공 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        data = {
            'fs_id': ObjectId(),
            'key': 'test'
        }

        mock_update_one.return_value = mock.Mock(matched_count=1)
        
        response = self.client.post(reverse('admin:manage_corp_fs_delete'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, mock_update_one.return_value.matched_count)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'message': '데이터 삭제가 완료되었습니다. 새로고침하여 확인해주세요.'})

    @mock.patch('pymongo.collection.Collection.update_one')
    @mock.patch('pymongo.collection.Collection.find_one')
    def test_corp_fs_add_success(self, mock_find_one, mock_update_one):
        """
        기업 재무제표 계정과목 추가 성공 테스트
        """
        email = 'testadmin@aimdat.com'
        password = 'testadmin1!'
        
        request = self.factory.get(reverse('admin:index'))
        self.client.login(request=request, username=email, password=password)

        data = {
            'fs_id': ObjectId(),
            'key': 'test',
            'value': '1234'
        }

        mock_find_one.return_value = None
        mock_update_one.return_value = mock.Mock(matched_count=1)
        
        response = self.client.post(reverse('admin:manage_corp_fs_add'), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, mock_update_one.return_value.matched_count)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'message': '계정과목 추가가 완료되었습니다. 새로고침하여 확인해주세요.'})