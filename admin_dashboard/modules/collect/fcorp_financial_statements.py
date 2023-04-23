"""
@created at 2023.04.23
@author OKS in Aimdat Team
"""
import csv
import glob
import json
import os
import platform
import pymongo
import re
import retry
import time

from django.http import HttpResponseServerError
from django.db.models import Q
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from ssl import SSLError
from webdriver_manager.chrome import ChromeDriverManager
from services.models.corp_id import CorpId

#django 앱 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

#secrets.json 경로
SECRETS_FILE = os.path.join(BASE_DIR, 'secrets.json')

def _get_fcorp_list():
    """
    금융 기업 목록 조회
    """
    try:
        #고용노동부_표준산업분류코드 csv 다운로드
        url = 'https://www.data.go.kr/data/15049591/fileData.do'
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(url)

        download_button = driver.find_element(By.XPATH, '//*[@id="tab-layer-file"]/div[2]/div[2]/a')
        download_button.click()
        time.sleep(3)

        with open(SECRETS_FILE, 'r') as secrets:
            download_path = json.load(secrets)['download_folder']
            file_path = glob.glob(download_path+'\\고용노동부_표준산업분류코드_*.csv')[0]

            with open(file_path, 'r', newline='') as file:
                file_content = csv.reader(file)

                # 금융업 목록만 파싱(대한민국 금융업: 64 ~ 66)
                fcorp_sector_list = []
                for row in file_content:
                    if row[1].startswith(('64', '65', '66')):
                        fcorp_sector_list.append(row[2])

        #현재 등록된 기업 목록 중 금융업종의 종목코드 검색
        stock_code_list = CorpId.objects.filter(Q(corp_sectors__in=fcorp_sector_list)).values_list('stock_code', flat=True)
        return stock_code_list

    except (CorpId.DoesNotExist, NoSuchElementException, FileNotFoundError):
        return HttpResponseServerError
    
@retry.retry(exceptions=SSLError, tries=10, delay=3)
def _crawl_dart(crawl_crp_list, year:int, quarter:int, fs_type=5, sleep_time=1):
    """
    open dart의 단일회사 재무제표 조회에서 금융 기업 목록 검색 후 재무제표 파싱
    """
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/singl/main.do'
    driver = webdriver.Chrome(ChromeDriverManager().install())
    
    fs_result = []
    # 검색 후 재무제표 획득
    for stock_code in crawl_crp_list:
        driver.get(url)
        print(stock_code)

        find_corp_button = driver.find_element(By.ID, 'btnOpenFindCrp')
        find_corp_button.click()
        time.sleep(sleep_time)

        # 회사명 검색
        input_stock_code = driver.find_element(By.XPATH, '//*[@id="textCrpNm"]')
        input_stock_code.click()
        input_stock_code.send_keys(stock_code)
        input_stock_code.send_keys(Keys.RETURN)
        time.sleep(sleep_time)

        try:
            element_present = EC.presence_of_element_located((By.XPATH, '//input[@type="checkbox"][@name="checkCorpSelect"]'))
            WebDriverWait(driver, timeout=1).until(element_present)
        except TimeoutException:
            continue

        # 새로운 체크박스 중 첫 번째 체크박스 클릭
        checkbox = driver.find_element(By.XPATH, '(//input[@type="checkbox"][@name="checkCorpSelect"])[1]')
        checkbox.click()

        search_button = driver.find_element(By.CLASS_NAME, 'btn_s_b')
        search_button.click()

        # 사업연도 검색(최대 5년)
        select_year_element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "selectYear")))
        select_year = Select(select_year_element)
        select_year.select_by_value(str(year))
        
        # 보고서명 선택 {1: 1분기보고서, 2: 반기보고서, 3: 3분기보고서, 4: 사업보고서}
        select_report_name_element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "reportCode")))
        select_report_name = Select(select_report_name_element)
        if quarter == 1:
            select_report_name.select_by_value('11013')
        elif quarter == 2:
            select_report_name.select_by_value('11012')
        elif quarter == 3:
            select_report_name.select_by_value('11014')
        elif quarter == 4:
            select_report_name.select_by_value('11011')

        # 재무제표 선택 {5: 개별재무제표, 0: 연결재무제표}
        select_financial_type_element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "selectToc")))
        select_financial_type = Select(select_financial_type_element)
        select_financial_type.select_by_value(str(fs_type))
        
        search_financial_statements_button = driver.find_element(By.ID, 'searchpng')
        search_financial_statements_button.click()
        time.sleep(sleep_time)

        # 재무제표 파싱
        try:
            iframe = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//div[@class="if_result02"]/iframe')))
        except TimeoutException:
            # iframe 결과가 없는 기업들은 재무제표가 존재하지 않으므로 넘어간다.
            continue

        driver.switch_to.frame(iframe)

        inner_html = BeautifulSoup(driver.page_source, 'html.parser')

        tables = inner_html.find_all('table')
        for table in tables:
            # 재무제표 dict
            fs_dict = dict()

            # 재무제표 여부 확인
            if len(table.find_all(name='th', string=re.compile(r'\s*?과\s*?목'))) > 0 or len(table.find_all(name='th', string=re.compile(r'제\s*?[0-9]+'))) > 0:

                # 종목코드 지정
                fs_dict['종목코드'] = str(stock_code)

                # 재무제표 금액 단위 파싱
                unit = inner_html.find(name='td', attrs={'valign': 'BOTTOM'}, string=re.compile(r'\s*?\(\s*?단위'))
                if unit:
                    fs_dict['단위'] = re.sub(r'\(단위\s*?:\s*?|\)', '', unit.get_text()).replace(' ', '')

                # 재무제표의 년도, 분기 설정
                fs_dict['년도'] = year
                fs_dict['분기'] = quarter

                # 가져온 재무제표의 종류 구분
                if len(table.find_all(string=re.compile(r'자\s*?본\s*?총\s*?계'))) > 0:
                    if fs_type == 5:
                        fs_dict['재무제표종류'] = '재무상태표'
                    elif fs_type == 0:
                        fs_dict['재무제표종류'] = '연결재무상태표'
                elif len(table.find_all(string=re.compile(r'.*?주\s*?당\s*?순?\s*?이\s*?익'))) > 0:
                        if fs_type == 5:
                            fs_dict['재무제표종류'] = '포괄손익계산서'
                        elif fs_type == 0:
                            fs_dict['재무제표종류'] = '연결포괄손익계산서'
                elif len(table.find_all(string=re.compile(r'현\s*?금\s*?흐\s*?름'))) > 0:
                    if fs_type == 5:
                        fs_dict['재무제표종류'] = '현금흐름표'
                    elif fs_type == 0:
                        fs_dict['재무제표종류'] = '연결현금흐름표'
                elif len(table.find_all(string=re.compile(r'.*?미\s*?처\s*?분'))) > 0:
                    # 이익잉여금처분계산서 제외
                    continue
                elif len(table.find_all(string=re.compile(r'\s*?[0-9]+년?\.?\s*?[0-9]+월?\.?\s*?[0-9]+일?'))) > 0:
                    # 자본변동표 제외
                    continue
                
                rows = table.find_all('tr')
                
                # 차변/대변 존재 여부 확인
                if len(table.find_all(name='th', attrs={'colspan': '2'}, string=re.compile(r'제\s*?[0-9]+'))) > 0:
                    for row in rows:

                        # 재무제표 표 헤더 건너뛰기
                        if row.find_all(name='th'):
                            continue
                        
                        tds = row.find_all('td')
                        if tds[0].attrs.get('colspan'):
                            # colspan이 합쳐져 있는 형태의 계정과목 생략
                            continue
                        else:
                            account_subject = tds[0].get_text() # 계정과목

                        # 재무제표 내에 주석이 존재하는 지 확인
                        if table.find(name='th', string=re.compile(r'\s*?주\s*?석')):
                            debit = tds[2].get_text().replace(',', '').replace(' ', '').strip() # 차변(왼쪽)
                            credit = tds[3].get_text().replace(',', '').replace(' ', '').strip() # 대변(오른쪽)

                            # 차변/대변의 숫자 존재 여부 확인
                            if debit != '' and credit == '':
                                if '(' in str(debit):
                                    fs_dict[account_subject] = str(debit).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(debit)
                            elif debit == '' and credit != '':
                                if '(' in str(credit):
                                    fs_dict[account_subject] = str(credit).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(credit)
                            elif debit == '' and credit == '':
                                continue
                        else:
                            debit = tds[1].get_text().replace(',', '').replace(' ', '').strip() # 차변(왼쪽)
                            credit = tds[2].get_text().replace(',', '').replace(' ', '').strip() # 대변(오른쪽)

                            # 차변/대변의 숫자 존재 여부 확인
                            if debit != '' and credit == '':
                                if '(' in str(debit):
                                    fs_dict[account_subject] = str(debit).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(debit).replace('-', '')
                            elif debit == '' and credit != '':
                                if '(' in str(credit):
                                    fs_dict[account_subject] = str(credit).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(credit)
                            elif debit == '' and credit == '':
                                continue
                else:
                    for row in rows:

                        # 재무제표 표 헤더 건너뛰기
                        if row.find_all(name='th'):
                            continue
                        
                        tds = row.find_all('td')
                        if tds[0].attrs.get('colspan'):
                            # colspan이 합쳐져 있는 형태의 계정과목 생략
                            continue
                        else:
                            account_subject = tds[0].get_text() # 계정과목

                        # 재무제표 내에 주석이 존재하는 지 확인
                        if table.find(name='th', string=re.compile(r'\s*?주\s*?석')):
                            value = tds[2].get_text().replace(',', '').replace(' ', '').strip() # 재무제표 값

                            # 각 계정과목의 값 존재 여부 확인
                            if value != '':
                                if '(' in str(value):
                                    fs_dict[account_subject] = str(value).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(value)
                            elif value == '':
                                continue
                        else:
                            value = tds[1].get_text().replace(',', '').replace(' ', '').replace('-', '') # 재무제표 값

                            # 각 계정과목의 값 존재 여부 확인
                            if value != '':
                                if '(' in str(value):
                                    fs_dict[account_subject] = str(value).replace('(', '-').replace(')', '')
                                else:
                                    fs_dict[account_subject] = str(value)
                            elif value == '':
                                continue

            else:
                # 재무제표가 아닌 테이블은 넘어간다.
                continue

            # 수집된 재무제표는 list에 저장(이익잉여금처분계산서, 자본변동표는 제외)
            if len(table.find_all(string=re.compile(r'.*?미\s*?처\s*?분'))) == 0 and len(table.find_all(string=re.compile(r'\s*?[0-9]+\.\s*?[0-9]+\.\s*?[0-9]+'))) == 0:
                fs_result.append(fs_dict)

    return fs_result
    
def _remove_file(file_path, system_name, folder=False):
    """
    사용한 파일 제거
    """
    if system_name == 'Windows':
        if folder:
            os.system('echo y | rd /s {} '.format(file_path))
        else:
            os.system('del {}'.format(file_path)) # Windows
    elif system_name == 'Linux':
        os.system('rm -rf {}'.format(file_path)) # Linux
    
def save_fcorp(year:int, quarter:int, fs_type=5):
    """
    금융 기업 재무제표 목록 저장
    """
    fcorp_list = _get_fcorp_list()
    crawl_result = _crawl_dart(fcorp_list, year, quarter, fs_type)

    if crawl_result:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["aimdat"]
        collection = db["financial_statements"]

        # MongoDB에 저장
        result = collection.insert_many(crawl_result)

        # 사용한 파일 제거
        with open(SECRETS_FILE, 'r') as secrets:
            download_path = json.load(secrets)['download_folder']
            file_path = glob.glob(download_path+'\\고용노동부_표준산업분류코드_*.csv')

            if len(file_path) > 0:
                system_name = platform.system()
                _remove_file(file_path[0], system_name)

        # 성공 여부 리턴
        if result:
            return True
        else:
            return False