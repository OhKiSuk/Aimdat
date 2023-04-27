"""
@created at 2023.04.21
@author JSU in Aimdat Team
"""

import json, os, pandas, time, shutil
from config.settings.base import get_secret
from django.apps import apps
import zipfile
import pymongo
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

def get_ifrs_xbrl_txt():
    # path 지정
    path = apps.get_app_config('admin_dashboard').path + '\\data\\'

    # 임시 폴더 생성
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(apps.get_app_config('admin_dashboard').path + '\\data')

    # 데이터 저장 위치 설정
    option = webdriver.ChromeOptions()
    option.add_experimental_option("prefs", {
        "download.default_directory": path
    })
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options = option)

    # 수집할 데이터
    year = [2022, 2021, 2020]
    quarter = ['1분기', '반기', '3분기', '사업']
    report = ['재무상태표', '손익계산서', '현금흐름표']

    # 크롤 시작
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do'
    driver.get(url)
    time.sleep(2)
    
    for y in year:
        btn_year = driver.find_element(By.XPATH, "//a[@title={}]".format(y))
        btn_year.click()

        for q in quarter:
            for r in report:
                try:
                    btn_report = driver.find_element(By.XPATH, "//a[@title='{} {}보고서 {} 다운로드']".format(y, q, r))
                    btn_report.click()
                    time.sleep(0.5)
                except NoSuchElementException:
                    print('데이터를 찾을 수 없습니다. {}, {}, {}'.format(y, q, r))

    time.sleep(2)

    # zip 압축 해제
    f_list = os.listdir(path)
    zip_files = [file for file in f_list if file.endswith('.zip')]

    for zip_file in zip_files:
        with zipfile.ZipFile(path + zip_file, 'r') as zip:
            files = zip.infolist()

            # 한글 깨짐 방지
            for file in files:
                file.filename = file.filename.encode('CP437').decode('euc-kr')
            
            zip.extract(file, path)

def txt_to_json():
    # path 지정 및 파일 선택
    path = apps.get_app_config('admin_dashboard').path + '\\data\\'
    f_list = os.listdir(path)
    txt_files = [file for file in f_list if file.endswith('.txt')]

    for txt_file in txt_files:
        df = pandas.read_csv(path + txt_file, sep='\t', encoding='CP949', dtype='unicode', header=0)
        name = str(txt_file)

        # 불필요 컬럼 제거
        unused_cols = df.columns.str.contains('Unnamed')
        df = df.drop(df[df.columns[unused_cols]], axis=1)
        unused_cols = df.columns.str.contains('전기')
        df = df.drop(df[df.columns[unused_cols]], axis=1)
        df = df.drop('결산월', axis=1)
        df = df.drop('통화', axis=1)
        df = df.drop('업종', axis=1)
        df = df.drop('업종명', axis=1)
        df = df.drop('시장구분', axis=1)
        df = df.drop('항목코드', axis=1)

        # 분기 데이터
        if '1분기' in name:
            quarter = '1'
        elif '반기' in name:
            quarter = '2'
        elif '3분기' in name:
            quarter = '3'
        elif '사업' in name:
            quarter = '4'
        else:
            quarter = '0'

        if quarter == 0:
            print('분기 값을 확인할 수 없습니다.')
            break

        # 년도, 분기, 당기 컬럼이름 변경
        df = df.rename(columns = {'결산기준일': '년도'})
        df = df.rename(columns = {'보고서종류': '분기'})
        df = df.rename(columns = {df.columns[6]: '당기'})

        # 종목코드 대괄호 제거
        df['종목코드'] = df['종목코드'].str.replace('[', '').str.replace(']', '')

        # 년도, 분기 값 변경
        df['년도'] = df['년도'].str[:4]
        df['분기'] = quarter

        # 값 콤마 제거
        df['당기'] = df['당기'].str.replace(',', '')

        df.to_json(path + name[0:name.rfind('_')] + '.json', orient = 'records', force_ascii=False)

def import_json():
    # path 지정 및 파일 선택
    path = apps.get_app_config('admin_dashboard').path + '\\data\\'
    f_list = os.listdir(path)
    json_files = [file for file in f_list if file.endswith('.json')]

    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements']

    for json_file in json_files:
        with open(path + json_file, encoding = 'utf-8') as f:
            for jsonObj in f:
                data = json.loads(jsonObj)

            collection.insert_many(data)

    client.close()
    shutil.rmtree(path)
