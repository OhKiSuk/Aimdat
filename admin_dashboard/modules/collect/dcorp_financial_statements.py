"""
@created at 2023.04.21
@author JSU in Aimdat Team

@modified at 2023.06.19
@author OKS in Aimdat Team
"""
import csv
import glob
import logging
import os
import pandas
import pymongo
import time
import shutil
import zipfile

from bson.decimal128 import Decimal128
from config.settings.base import get_secret
from django.db.models import Q
from django.http import HttpResponseServerError
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

from services.models.corp_id import CorpId
from ..remove.remove_files import remove_files

DOWNLOAD_PATH = get_secret('download_folder')

LOGGER = logging.getLogger(__name__)

def _get_ifrs_xbrl_txt(years, quarters):
    # path 지정
    path = os.path.join(DOWNLOAD_PATH, 'fs_zips')

    # 임시 폴더 생성
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(os.path.join(DOWNLOAD_PATH, 'fs_zips'))

    # 데이터 저장 위치 설정
    option = webdriver.ChromeOptions()
    option.add_experimental_option("prefs", {
        "download.default_directory": path
    })
    option.add_argument("--headless")
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options = option)

    # 수집할 데이터
    report = ['재무상태표', '손익계산서', '현금흐름표']

    # 크롤 시작
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do'
    try:
        driver.get(url)
    except TimeoutException as e:
        print(e)
    except WebDriverException as e:
        print(e)
    time.sleep(2)
    
    for y in years:
        btn_year = driver.find_element(By.XPATH, "//a[@title={}]".format(y))
        btn_year.click()

        for q in quarters:
            for r in report:
                try:
                    btn_report = driver.find_element(By.XPATH, "//a[@title='{} {}보고서 {} 다운로드']".format(y, q, r))
                except NoSuchElementException:
                    # A403 로깅
                    LOGGER.error('[A403] 비금융 재무제표 다운로드 실패. {}, {}, {}'.format(y, q, r))
                
                btn_report.click()
                time.sleep(0.5)

    time.sleep(2)

    # zip 압축 해제
    f_list = os.listdir(path)
    zip_files = [file for file in f_list if file.endswith('.zip')]

    for zip_file in zip_files:
        with zipfile.ZipFile(os.path.join(path, zip_file), 'r') as zip:
            files = zip.infolist()

            # 한글 깨짐 방지
            for file in files:
                file.filename = file.filename.encode('CP437').decode('euc-kr')
            
                zip.extract(file, path)

def _get_dcorp_list():
    """
    비금융 기업 목록 조회
    """
    try:
        #고용노동부_표준산업분류코드 csv 다운로드
        url = 'https://www.data.go.kr/data/15049591/fileData.do'
        option = webdriver.ChromeOptions()
        option.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_PATH
        })
        option.add_argument("--headless")
        option.add_argument('--no-sandbox')
        option.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=option)
        driver.get(url)
        time.sleep(5)
        
        download_button = driver.find_element(By.XPATH, '//*[@class="tab-content active"]/div[2]/div[2]/a')
        # A005 로깅
        try:
            driver.execute_script("arguments[0].click();", download_button)
            time.sleep(3)
        except:
            LOGGER.error('[A005] 산업분류코드 다운로드 실패.')

        file_path = glob.glob(os.path.join(DOWNLOAD_PATH, '고용노동부_표준산업분류코드_*.csv'))[0]

        with open(file_path, 'r', newline='', encoding='CP949') as file:
            file_content = csv.reader(file)

            # 비금융기업만 파싱(대한민국 금융업: 64 ~ 66)
            fcorp_sector_list = []
            for row in file_content:
                if not row[1].startswith(('64', '65', '66')):
                    fcorp_sector_list.append(row[2])

        #현재 등록된 기업 목록 중 비금융업종의 종목코드 검색
        stock_code_list = CorpId.objects.filter(Q(corp_sectors__in=fcorp_sector_list)).values_list('stock_code', flat=True)

        return stock_code_list

    except (CorpId.DoesNotExist, NoSuchElementException, FileNotFoundError):
        # A006 로깅
        LOGGER.error('[A006] 산업분류코드 파싱 실패.')
        return HttpResponseServerError

def _parse_txt(stock_codes):
    """
    txt 파일에서 재무제표 추출 후 dict로 변환
    """
    # path 지정 및 파일 선택
    path = os.path.join(DOWNLOAD_PATH, 'fs_zips')
    f_list = os.listdir(path)
    txt_files = [file for file in f_list if file.endswith('.txt')]

    fs_dict_list = []
    for txt_file in txt_files:
        df = pandas.read_csv(os.path.join(path, txt_file), sep='\t', encoding='CP949', dtype='unicode', header=0)

        # 손익계산서 건너뛰기
        if '_02_' in txt_file:
            continue

        # 불필요한 값 제거
        unused_cols = df.columns.str.contains('전기|Unnamed')
        df = df.drop(df[df.columns[unused_cols]], axis=1)
        
        # 재무제표 추출
        for stock_code in stock_codes:
            fs_dict = {}
            
            # 종목코드와 일치하는 데이터 조회
            match_rows = df.loc[df['종목코드'] == '['+stock_code+']']

            # 종목코드와 일치하는 값이 없으면 건너뛰기
            if len(match_rows) == 0:
                continue

            # 종목코드 저장
            fs_dict['종목코드'] = stock_code

            # 재무제표종류 저장
            if '연결' in txt_file:
                fs_dict['재무제표종류'] = '연결' + df.iloc[0]['재무제표종류'].split(',')[0]
            else:
                fs_dict['재무제표종류'] = '별도' + df.iloc[0]['재무제표종류'].split(',')[0]
            
            # 분기 저장
            if '1분기' in txt_file:
                quarter = 1
            elif '반기' in txt_file:
                quarter = 2
            elif '3분기' in txt_file:
                quarter = 3
            elif '사업' in txt_file:
                quarter = 4
            
            fs_dict['년도'] = int(df.iloc[0]['결산기준일'][:4])
            fs_dict['분기'] = quarter
            fs_dict['단위'] = '원'
            
            # 계정과목 저장
            for _, row in match_rows.iterrows():
                if row.filter(regex=r'(?!.*3개월)당기').empty:
                    fs_dict[row['항목명']] = None 
                else:
                    if row.filter(regex=r'(?!.*3개월)당기').iloc[0] == 'nan':
                        fs_dict[row['항목명']] = None
                    else:
                        fs_dict[row['항목명']] = Decimal128(str(row.filter(regex=r'(?!.*3개월)당기').iloc[0]).replace(',', ''))

            fs_dict_list.append(fs_dict)
    
    # dict 목록 리턴
    return fs_dict_list

def save_dcorp(years, quarters):

    # 재무제표 다운로드
    _get_ifrs_xbrl_txt(years, quarters)

    # 비금융기업 기업목록 조회
    stock_codes = _get_dcorp_list()

    # 재무제표 파싱
    fs_lists = _parse_txt(stock_codes)
    
    if len(fs_lists) > 0:
        client = pymongo.MongoClient('localhost:27017')
        db = client['aimdat']
        collection = db['financial_statements']

        # 데이터 저장
        for fs in fs_lists:
            if collection.find_one({'종목코드': fs['종목코드'], '년도': fs['년도'], '분기': fs['분기'], '재무제표종류': fs['재무제표종류']}):
                collection.delete_one({'종목코드': fs['종목코드'], '년도': fs['년도'], '분기': fs['분기'], '재무제표종류': fs['재무제표종류']})
                collection.insert_one(fs)
            else:
                collection.insert_one(fs)

        client.close()

        # 파일 삭제
        file_path = glob.glob(os.path.join(DOWNLOAD_PATH, '고용노동부_표준산업분류코드_*.csv'))
        folder_path = glob.glob(os.path.join(DOWNLOAD_PATH, 'fs_zips'))

        if len(file_path) > 0:
            remove_files(file_path[0])

        if len(folder_path) > 0:
            remove_files(folder_path[0], folder=True)

        return True

    # 파일 삭제
    file_path = glob.glob(os.path.join(DOWNLOAD_PATH, '고용노동부_표준산업분류코드_*.csv'))
    folder_path = glob.glob(os.path.join(DOWNLOAD_PATH, 'fs_zips'))

    if len(file_path) > 0:
        remove_files(file_path[0])

    if len(folder_path) > 0:
        remove_files(folder_path[0], folder=True)

    return False