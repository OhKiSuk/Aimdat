"""
@created at 2023.05.18
@author OKS in Aimdat Team

@modified at 2023.06.15
@author JSU in Aimdat Team
"""
import csv
import glob
import logging
import os
import requests
import time
import xml.etree.ElementTree as ET
import zipfile

from config.settings.base import get_secret
from requests import ConnectionError, ConnectTimeout, Timeout, RequestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from webdriver_manager.chrome import ChromeDriverManager
from ..api_error.open_dart_api_error import check_open_dart_api_error
from ..remove.remove_files import remove_files

LOGGER = logging.getLogger(__name__)

def _download_corp_code():
    """
    Opendart의 고유번호 파일 다운로드
    """
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    params = {
        'crtfc_key': get_secret('crtfc_key') 
    }
    response = requests.get(url, params=params)

    downlaod_path = get_secret('download_folder')

    # A003 로깅
    try:
        with open(downlaod_path+'\\corpCode.zip', 'wb') as file:
            file.write(response.content)
    except:
        LOGGER.error('[A003] CORPCODE 다운로드 실패.')

def _unzip_corp_code():
    """
    Opendart의 고유번호 파일 압축해제
    """
    download_path = get_secret('download_folder')

    # A004 로깅
    try:
        with zipfile.ZipFile(download_path+'\\corpCode.zip', 'r') as zip_file:
            zip_file.extract('CORPCODE.xml', download_path)
    except:
        LOGGER.error('[A004] CORPCODE 압축 해제 실패.')

def _collect_corp_info(stock_codes):
    """
    기업 정보 수집
    """
    url = 'https://opendart.fss.or.kr/api/company.json'
    params = {
        'crtfc_key': get_secret('crtfc_key')
    }

    # corp_code 조회
    download_path = get_secret('download_folder')
    corp_code_tree = ET.parse(download_path+'\\CORPCODE.xml')
    corp_code_root = corp_code_tree.getroot()

    corp_info_data_list = []
    for stock_code in stock_codes:
        
        corp_info_data = {}
        for element in corp_code_root.iter('list'):
            stock_code_element = element.find('stock_code').text

            if str(stock_code_element) == str(stock_code):
                params['corp_code'] = element.find('corp_code').text

                # API 호출 로깅
                try:
                    response = requests.get(url, params=params, verify=False)
                except ConnectTimeout:
                    LOGGER.error('[A013] Requests 연결 타임아웃 에러')
                except ConnectionError:
                    LOGGER.error('[A012] Requests 연결 에러')
                except Timeout:
                    LOGGER.error('[A011] Requests 타임아웃 에러')
                except RequestException:
                    LOGGER.error('[A010] Requests 범용 에러')

                time.sleep(0.3)

                response_to_json = response.json()
                if response_to_json['status'] == '000':
                    corp_info_data['corp_id'] = CorpId.objects.get(stock_code=stock_code)
                    corp_info_data['corp_homepage_url'] = response_to_json['hm_url'] # 홈페이지 주소
                    corp_info_data['corp_settlement_month'] = response_to_json['acc_mt'] # 결산월
                    corp_info_data['corp_ceo_name'] = response_to_json['ceo_nm'] # 대표자 명
                    corp_info_data['induty_code'] = response_to_json['induty_code'] # 산업분류코드

                    corp_info_data_list.append(corp_info_data)
                else:
                    # OpenDartApi 예외처리
                    check_open_dart_api_error(response_to_json['status'])
    
    return corp_info_data_list

def _download_induty_code():
    """
    공공데이터포털 고용노동부_표준산업분류코드에서 산업분류코드 다운로드
    """
    url = 'https://www.data.go.kr/data/15049591/fileData.do'
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(5)

    # A005 로깅
    try:
        download_button = driver.find_element(By.XPATH, '//*[@class="tab-content active"]/div[2]/div[2]/a')
    except NoSuchElementException:
        LOGGER.error('[A005] 산업분류코드 다운로드 경로 에러.')

    time.sleep(3)
    download_button.click()

def _parse_induty_code(corp_id, induty_code):
    """
    산업분류코드를 파싱 후 저장
    """
    download_path = get_secret('download_folder')
    file_path = glob.glob(download_path+'\\고용노동부_표준산업분류코드_*.csv')[0]

    with open(file_path, 'r', newline='') as file:
        # A006 로깅
        try:
            file_content = csv.reader(file)
        except:
            LOGGER.error('[A006] 산업분류코드 파싱 실패.')

        for row in file_content:
            if row[1] == induty_code:
                CorpId.objects.filter(id=corp_id).update(
                    corp_sectors=row[2]
                )

def save_corp_info():
    """
    기업 정보 저장

    성공 시 True 리턴, 실패 시 False 리턴, 기본 리턴값은 False임
    """
    _download_corp_code()
    _unzip_corp_code()

    stock_codes = CorpId.objects.all().values_list('stock_code', flat=True)
    result = _collect_corp_info(stock_codes)
    
    if len(result) > 0:
        # 산업분류코드 다운로드
        _download_induty_code()

        for corp_info in result:
            # CorpId에 섹터명(산업분류명) 파싱 후 저장(Corp 섹터가 없는 것만)
            if CorpId.objects.filter(corp_sectors=None).exists():
                _parse_induty_code(corp_info['corp_id'].id, corp_info['induty_code'])

            # 중복 저장 방지
            if not CorpInfo.objects.filter(corp_id=corp_info['corp_id']).exists():
                CorpInfo.objects.create(
                    corp_id = corp_info['corp_id'],
                    corp_homepage_url = corp_info['corp_homepage_url'],
                    corp_settlement_month = corp_info['corp_settlement_month'],
                    corp_ceo_name = corp_info['corp_ceo_name']
                )
            else:
                # 기존 기업 정보 갱신
                CorpInfo.objects.filter(corp_id=corp_info['corp_id']).update(
                    corp_id = corp_info['corp_id'],
                    corp_homepage_url = corp_info['corp_homepage_url'],
                    corp_settlement_month = corp_info['corp_settlement_month'],
                    corp_ceo_name = corp_info['corp_ceo_name']
                )

        download_path = get_secret('download_folder')
        file_path = glob.glob(os.path.join(download_path, '고용노동부_표준산업분류코드_*.csv'))[0]

        # 고용노동부_표준산업분류코드 제거
        remove_files(file_path)

        # corp_code 관련 파일 제거
        remove_files(os.path.join(get_secret('download_folder'), 'CORPCODE.xml'))
        remove_files(os.path.join(get_secret('download_folder'), 'corpCode.zip'))

        return True

    # corp_code 관련 파일 제거
    remove_files(os.path.join(get_secret('download_folder'), 'CORPCODE.xml'))
    remove_files(os.path.join(get_secret('download_folder'), 'corpCode.zip'))

    return False