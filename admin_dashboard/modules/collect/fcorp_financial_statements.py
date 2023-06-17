"""
@created at 2023.04.23
@author OKS in Aimdat Team

@modified at 2023.06.17
@author JSU in Aimdat Team
"""
import csv
import glob
import json
import logging
import os
import pymongo
import re
import time

from bson.decimal128 import Decimal128
from django.http import HttpResponseServerError
from django.db.models import Q
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from services.models.corp_id import CorpId
from ..remove.remove_files import remove_files
from config.settings.base import get_secret

#django 앱 최상위 경로
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

#secrets.json 경로
SECRETS_FILE = os.path.join(BASE_DIR, 'secrets.json')

LOGGER = logging.getLogger(__name__)

def _get_fcorp_list():
    """
    금융 기업 목록 조회
    """
    try:
        #고용노동부_표준산업분류코드 csv 다운로드
        url = 'https://www.data.go.kr/data/15049591/fileData.do'
        option = webdriver.ChromeOptions()
        option.add_experimental_option("prefs", {
            "download.default_directory": get_secret('download_folder')
        })
        option.add_argument("--headless")
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=option)
        driver.get(url)
        time.sleep(5)

        # A005 로깅
        try:
            download_button = driver.find_element(By.XPATH, '//*[@id="tab-layer-file"]/div[2]/div[2]/a')
        except:
            LOGGER.error('[A005] 산업분류코드 다운로드 경로 에러.')
        
        driver.execute_script("arguments[0].click();", download_button)
        time.sleep(3)

        with open(SECRETS_FILE, 'r') as secrets:
            download_path = json.load(secrets)['download_folder']
            file_path = glob.glob(download_path+'/고용노동부_표준산업분류코드_*.csv')[0]

            with open(file_path, 'r', newline='', encoding='CP949') as file:
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
        # A006 로깅
        LOGGER.error('[A006] 산업분류코드 파싱 실패.')
        return HttpResponseServerError
    
def _crawl_dart(crawl_crp_list, year, quarter, fs_type=5, sleep_time=1):
    """
    open dart의 단일회사 재무제표 조회에서 금융 기업 목록 검색 후 재무제표 파싱
    """
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/singl/main.do'
    option = webdriver.ChromeOptions()
    option.add_argument("--headless")
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=option)
    
    fs_result = []
    # 검색 후 재무제표 획득
    for stock_code in crawl_crp_list:
        try:
            driver.get(url)
        except TimeoutException as e:
            LOGGER.info(e, stock_code, year, quarter, fs_type)
        except WebDriverException as e:
            LOGGER.info(e, stock_code, year, quarter, fs_type)

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
        except NoSuchElementException:
            # A504 로깅
            LOGGER.error('[A504] 종목코드로 검색된 회사명이 없음. {}, {}, {}'.format(stock_code, year, quarter, fs_type))
            continue
        try:
            WebDriverWait(driver, timeout=1).until(element_present)
        except TimeoutException as e:
            LOGGER.info(e, stock_code, year, quarter, fs_type)

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
        select_report_name_element = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, 'reportCode')))
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
            # A505 로깅
            LOGGER.error('[A505] 재무제표 조회 결과가 반환되지 않음. {}, {}, {}, {}'.format(stock_code, year, quarter, fs_type))
            continue

        driver.switch_to.frame(iframe)

        inner_html = BeautifulSoup(driver.page_source, 'html.parser')

        tables = inner_html.find_all('table')
        for table in tables:
            # 재무제표 dict
            fs_dict = dict()

            # 재무제표 여부 확인
            if len(table.find_all(string=re.compile(r'과(\s|&nbsp;)*목(\s|&nbsp;)*$'))) > 0 or \
                len(table.find_all(string=re.compile(r'제(\s|&nbsp;)*[0-9]+(\s|&nbsp;)*(\(당\))?기?말?(\s|&nbsp;)*((1|3)분기|반기)?(\s|&nbsp;)*말?$'))) > 0 or \
                len(table.find_all(string=re.compile(r'구(\s|&nbsp;)*분(\s|&nbsp;)*$'))) > 0:

                # 종목코드 지정
                fs_dict['종목코드'] = str(stock_code)

                # 재무제표 금액 단위 파싱
                unit = inner_html.find(string=re.compile(r'\((\s|&nbsp;)?단위'))
                if unit:
                    fs_dict['단위'] = re.sub(r'(\s|&nbsp;)|단위|:|\(|\)', '', unit.get_text()).strip()

                # 재무제표의 년도, 분기 설정
                fs_dict['년도'] = year
                fs_dict['분기'] = quarter

                if len(table.find_all(string=re.compile(r'(\s|&nbsp;)*부(\s|&nbsp;)*채(\s|&nbsp;)*총(\s|&nbsp;)*계'))) > 0:
                    if fs_type == 5:
                        fs_dict['재무제표종류'] = '별도재무상태표'
                    elif fs_type == 0:
                        fs_dict['재무제표종류'] = '연결재무상태표'
                elif len(table.find_all(string=re.compile(r'주(\s|&nbsp;)*당'))) > 0 and len(table.find_all(string=re.compile(r'미처분'))) == 0 and len(table.find_all(string=re.compile(r'임의적립금'))) == 0 and len(table.find_all(string=re.compile(r'주식할인발행차금'))) == 0 or\
                      len(table.find_all(string=re.compile(r'금융수익'))) > 0 and len(table.find_all(string=re.compile(r'미처분'))) == 0 and len(table.find_all(string=re.compile(r'임의적립금'))) == 0 and len(table.find_all(string=re.compile(r'주식할인발행차금'))) == 0 and len(table.find_all(string=re.compile(r'현금성자산'))) == 0:
                        if fs_type == 5:
                            fs_dict['재무제표종류'] = '별도포괄손익계산서'
                        elif fs_type == 0:
                            fs_dict['재무제표종류'] = '연결포괄손익계산서'
                elif len(table.find_all(string=re.compile(r'현(\s|&nbsp;)*금(\s|&nbsp;)*성(\s|&nbsp;)*자(\s|&nbsp;)*산'))) > 0 or len(table.find_all(string=re.compile(r'기(\s|&nbsp;)*초(\s|&nbsp;)*의?(\s|&nbsp;)*현(\s|&nbsp;)*금'))) > 0:
                    if fs_type == 5:
                        fs_dict['재무제표종류'] = '별도현금흐름표'
                    elif fs_type == 0:
                        fs_dict['재무제표종류'] = '연결현금흐름표'
                else:
                    continue
                
                rows = table.find_all('tr')
                # 차변/대변 존재 여부 확인
                if len(table.find_all(attrs={'colspan': '2'})) and len(table.find_all(string=re.compile(r'제(\s|&nbsp;)*[0-9]+(\s|&nbsp;)*(\(당\))?기?말?(\s|&nbsp;)*((1|3)분기|반기)?(\s|&nbsp;)*말?$'))) > 0 or \
                    len(table.find_all(attrs={'colspan': '2'})) and len(table.find_all(string=re.compile(r'(3(\s|&nbsp;)?개(\s|&nbsp;)*월|누(\s|&nbsp;)*적(\s|&nbsp;)*)'))) > 0:
                    for row in rows:
                        # 재무제표 표 헤더 건너뛰기
                        if row.find_all(name='th') or len(row.find_all(string=re.compile(r'과(\s|&nbsp;)*목$'))) > 0 or\
                              len(row.find_all(string=re.compile(r'제(\s|&nbsp;)*[0-9]+(\s|&nbsp;)*(\(당\))?기?말?(\s|&nbsp;)*((1|3)분기|반기)?(\s|&nbsp;)*말?$'))) > 0 or\
                                  len(row.find_all(string=re.compile(r'(3(\s|&nbsp;)?개(\s|&nbsp;)*월|누(\s|&nbsp;)*적(\s|&nbsp;)*)'))) > 0:
                            continue
                        
                        tds = row.find_all('td')
                        if tds[0].attrs.get('colspan'):
                            # colspan이 합쳐져 있는 형태의 계정과목 생략
                            continue
                        else:
                            account_subject = tds[0].get_text() # 계정과목

                        # row가 합쳐져 있는 형태를 찾은 경우 log 저장 후 넘김
                        rowspan_tds = [td for td in tds if td.has_attr('rowspan')]
                        if len(rowspan_tds) > 0 or len(row.find_all(name='td')) == 1:
                            # A503 로깅
                            LOGGER.info('[A503] 합쳐진 row가 발견됨. {}, {}, {}, {}, {}'.format(stock_code, year, quarter, fs_type, tds[0].get_text()))
                            continue

                        # 표 헤더 부분의 주석 존재 확인
                        if table.find(string=re.compile(r'주(\s|&nbsp;)*석$')):
                            debit = re.findall(r'\(?\d+\)?', tds[2].get_text().replace(',', '')) # 차변(왼쪽)
                            credit = re.findall(r'\(?\d+\)?', tds[3].get_text().replace(',', '')) # 대변(오른쪽)

                            # 차변/대변의 숫자 존재 여부 확인
                            if debit:
                                # 음수/양수 구분
                                if '(' in str(debit[0]):
                                    fs_dict[account_subject] = Decimal128(str(debit[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(debit[0]).replace('(', '').replace(')', ''))
                            elif credit:
                                if '(' in str(credit[0]):
                                    fs_dict[account_subject] = Decimal128(str(credit[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(credit[0]).replace('(', '').replace(')', ''))
                        else:
                            debit = re.findall(r'\(?\d+\)?', tds[1].get_text().replace(',', '')) # 차변(왼쪽)
                            credit = re.findall(r'\(?\d+\)?', tds[2].get_text().replace(',', '')) # 대변(오른쪽)

                            # 차변/대변의 숫자 존재 여부 확인
                            if debit:
                                # 음수/양수 구분
                                if '(' in str(debit[0]):
                                    fs_dict[account_subject] = Decimal128(str(debit[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(debit[0]).replace('(', '').replace(')', ''))
                            elif credit:
                                # 음수/양수 구분
                                if '(' in str(credit[0]):
                                    fs_dict[account_subject] = Decimal128(str(credit[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(credit[0]).replace('(', '').replace(')', ''))
                else:
                    for row in rows:
                        # 재무제표 표 헤더 건너뛰기
                        if row.find_all(name='th') or len(row.find_all(string=re.compile(r'과(\s|&nbsp;)*목$'))) > 0 or\
                              len(row.find_all(string=re.compile(r'제(\s|&nbsp;)*[0-9]+(\s|&nbsp;)*(\(당\))?기?말?(\s|&nbsp;)*((1|3)분기|반기)?(\s|&nbsp;)*말?$'))) > 0 or\
                                  len(row.find_all(string=re.compile(r'(3(\s|&nbsp;)?개(\s|&nbsp;)*월|누(\s|&nbsp;)*적(\s|&nbsp;)*)'))) > 0:
                            continue
                        
                        tds = row.find_all('td')
                        if tds[0].attrs.get('colspan'):
                            # colspan이 합쳐져 있는 형태의 계정과목 생략
                            continue
                        else:
                            account_subject = tds[0].get_text() # 계정과목

                        # 표 헤더 부분의 주석 존재 확인
                        if table.find(string=re.compile(r'주(\s|&nbsp;)*석$')):
                            value = re.findall(r'\(?\d+\)?', tds[2].get_text().replace(',', ''))

                            # 각 계정과목의 값 존재 여부 확인
                            if value:
                                # 음수/양수 구분
                                if '(' in str(value[0]):
                                    fs_dict[account_subject] = Decimal128(str(value[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(value[0]).replace('(', '').replace(')', ''))
                        else:
                            value = re.findall(r'\(?\d+\)?', tds[1].get_text().replace(',', ''))

                            # 각 계정과목의 값 존재 여부 확인
                            if value:
                                # 음수/양수 구분
                                if '(' in str(value[0]):
                                    fs_dict[account_subject] = Decimal128(str(value[0]).replace('(', '-').replace(')', ''))
                                else:
                                    fs_dict[account_subject] = Decimal128(str(value[0]).replace('(', '').replace(')', ''))
            else:
                # 재무제표가 아닌 테이블은 넘어간다.
                continue
            
            fs_result.append(fs_dict)

    return fs_result
    
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

        # 데이터 저장
        for fs in crawl_result:
            if collection.find_one({'종목코드': fs['종목코드'], '년도': fs['년도'], '분기': fs['분기'], '재무제표종류': fs['재무제표종류']}):
                collection.delete_one({'종목코드': fs['종목코드'], '년도': fs['년도'], '분기': fs['분기'], '재무제표종류': fs['재무제표종류']})
                collection.insert_one(fs)
            else:
                collection.insert_one(fs)

        client.close()

        # 사용한 파일 제거
        with open(SECRETS_FILE, 'r') as secrets:
            download_path = json.load(secrets)['download_folder']
            file_path = glob.glob(os.path.join(download_path, '고용노동부_표준산업분류코드_*.csv'))

            if len(file_path) > 0:
                remove_files(file_path[0])

        return True

    # 사용한 파일 제거
    with open(SECRETS_FILE, 'r') as secrets:
        download_path = json.load(secrets)['download_folder']
        file_path = glob.glob(os.path.join(download_path, '고용노동부_표준산업분류코드_*.csv'))

        if len(file_path) > 0:
            remove_files(file_path[0])

    return False