"""
@created at 2023.04.04
@author cslee in Aimdat Team

@modified at 2023.04.17
@author OKS in Aimdat Team
"""
import json        
import os
import pandas as pd
import requests
import retry    
import sys
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

dir_collect = os.path.dirname(__file__)
dir_modules = os.path.dirname(dir_collect)
dir_admin_dashboard = os.path.dirname(dir_modules)
dir_aimdat = os.path.dirname(dir_admin_dashboard)
sys.path.append(dir_aimdat)
from admin_dashboard.models.last_collect_date import LastCollectDate
from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice

def _get_new_corp_list():
    try:
        corps = CorpId.objects.filter(corp_isin=None)
        stock_codes = [corp.stock_code for corp in corps]
        return stock_codes
    except CorpId.DoesNotExist:
        return []

def _get_secrets(key):
    secrets = json.load(open(os.path.join(dir_aimdat, 'secrets.json')))
    value = secrets[key]
    return value

@retry.retry(exceptions=[TimeoutError, ValueError], tries=10)
def _collect_new_corps_stocks(decimal_places=6):
    url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo'
    service_key = _get_secrets('data_portal_key')
    corp_list = _get_new_corp_list()
    n = len(corp_list)

    fail_list = []
    for i in range(n):
        stock_code = corp_list[i]
        params = {'serviceKey':service_key, 'numOfRows':100000000, 'pageNo':1, 'resultType':'json', 'beginBasDt':20200102, 'likeSrtnCd':stock_code}

        try:
            res = requests.get(url, params=params, verify=False)
        except TimeoutError:
            time.sleep(60)
        except ValueError:
            fail_list.append([stock_code, 'json decode error at:' + datetime.now()])
            continue
                
        res_data = res.json()
        dict_list = res_data['response']['body']['items']['item']
 
        basDt, srtnCd, isinCd, mrktCtg, clpr, vs, fltRt, mkp, hipr, lopr, trqu, trPrc, lstgStCnt, mrktTotAmt = \
        'basDt', 'srtnCd', 'isinCd', 'mrktCtg', 'clpr', 'vs', 'fltRt', 'mkp', 'hipr', 'lopr', 'trqu', 'trPrc', 'lstgStCnt', 'mrktTotAmt'

        if len(dict_list) < 1:
            fail_list.append([stock_code, 'api_result_fail'])
            continue
        # corpID
        tmp = dict_list[0]
        stock_code = tmp[srtnCd]
        corp_isin = tmp[isinCd]
        corp_market = tmp[mrktCtg]
        corp_country = corp_isin[:2]

        try:
            id_data = CorpId.objects.get(stock_code=stock_code)
            id_data.corp_isin = corp_isin
            id_data.corp_market = corp_market
            id_data.corp_country = corp_country
            id_data.save()
        except CorpId.DoesNotExist:
            fail_list.append([stock_code, 'corp_not_exist'])
            continue

        # stockPrice
        for x in dict_list:
            trade_date = x[basDt]
            tmp = [x[mkp], x[hipr], x[lopr], x[clpr], x[lstgStCnt], x[mrktTotAmt], x[trqu], x[trPrc], x[vs]]
            tmp = [round(float(x), ndigits=decimal_places) for x in tmp]
            open_price, high_price, low_price, close_price, total_stock, market_capitalization, trade_quantity, trade_price, change_price = tmp
            # preprocessing for change_rate
            tmp_list = x[fltRt].split('.')
            if tmp_list[0] == '-':
                tmp_list[0] = '-0'
            elif tmp_list[0] == '':
                tmp_list[0] = '0'
            if len(tmp_list) < 2:
                tmp_list.append('0')
            value = float('.'.join(tmp_list))
            change_rate = round(value, decimal_places)

            trade_date = trade_date[0:4] + '-' + trade_date[4:6] + '-' + trade_date[6:8]

            try:
                # 데이터 중복저장 예방
                sp_data = StockPrice.objects.get(corp_id=id_data, trade_date=trade_date)
                continue 
            except StockPrice.DoesNotExist:
                sp_data = StockPrice(
                    corp_id=id_data,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    trade_date=trade_date,
                    total_stock=total_stock,
                    market_capitalization=market_capitalization,
                    trade_quantity=trade_quantity,
                    trade_price=trade_price,
                    change_price=change_price,
                    change_rate=change_rate,
                )
            sp_data.save()

    return fail_list

def _remove_file(file_path, operate_system, folder=False):
    if operate_system == 'win':
        if folder:
            os.system('echo y | rd /s {} '.format(file_path))
        else:
            os.system('del {}'.format(file_path)) 
    elif operate_system == 'linux':
        os.system('rm -rf {}'.format(file_path))

def _crawl_krx_data(driver:webdriver.Chrome, date):
    # 날짜 기입
    a = driver.find_element(By.XPATH, "//input[@name='trdDd']")
    a.click()
    a.send_keys(Keys.CONTROL + "A")
    a.send_keys(date.strftime('%Y%m%d'))
    # 조회
    a = driver.find_element(By.XPATH, "//a[@name='search']")
    a.click()
    time.sleep(2)
    # 종가가 없다 -> 휴장이다 -> 넘어간다
    a = driver.find_element(By.XPATH, "//td[@data-bind='TDD_CLSPRC']")
    if a.text == '-':
        return 6
    # 다운로드 버튼
    src = 'CI-MDI-UNIT-DOWNLOAD'
    a = driver.find_element(By.XPATH, "//button[@class='{}']".format(src))
    a.click()
    time.sleep(2)
    # csv 버튼
    src = 'csv'
    a = driver.find_element(By.XPATH, "//div[@data-type='{}']".format(src))
    a.click()
    time.sleep(2) 
    time.sleep(10) # download time
    
    return 0

def _collect_stocks(last_date:datetime, today=datetime.today().date(), decimal_places=6, operate_system='win'):
    # init
    driver = webdriver.Chrome(ChromeDriverManager().install())
    download_folder = _get_secrets('download_folder')

    url = 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201'
    driver.get(url)
    a = driver.find_elements(By.XPATH, "//a[@href='javascript:void(0);']")
    for e in a:
        if e.text == '주식':
            e.click()
            break
    a = driver.find_elements(By.XPATH, "//a[@href='javascript:void(0);']")
    for e in a:
        if e.text == '종목시세':
            e.click()
            break
    a = driver.find_elements(By.XPATH, "//a[@href='javascript:void(0);']")
    for e in a:
        if e.text == '전종목 시세':
            e.click()
            break

    fail_list = []
    date = last_date + timedelta(days=1)
    while date <= today:
        cnt = 0
        while(cnt < 5): # 최대 50초 대기
            try:
                cnt = _crawl_krx_data(driver, date)
                break
            except NoSuchElementException:
                time.sleep(10)
                cnt += 1
        if cnt == 5:    
            fail_list.append([date, 'timeout'])
            date += timedelta(days=1)
            continue
        if cnt == 6: # 휴장
            date += timedelta(days=1)
            continue

        today_str = today.strftime("%Y%m%d")
        csv_name = ''
        for f_name in os.listdir(download_folder):
            if f_name.startswith('data_') & f_name.endswith('{}.csv'.format(today_str)):
                csv_name = f_name
                break        
        csv_path = download_folder+'\\'+csv_name
        # data parsing and save
        try:
            df = pd.read_csv(csv_path, encoding='cp949')
        except FileNotFoundError:
            fail_list.append([date, 'file_not_found'])
            continue

        cols = df.columns[0:1].values.tolist() + df.columns[4:].values.tolist()
        df = df[cols]
        n = len(df)
        for i in range(n):
            row = df.iloc[i]
            stock_code = row[0]
            try:
                corp_id = CorpId.objects.get(stock_code=stock_code)
            except CorpId.DoesNotExist:
                continue
            
            # data processing
            tmp = row[1:]
            tmp = [round(float(x), ndigits=decimal_places) for x in tmp]
            close_price, change_price, change_rate, open_price, \
            high_price, low_price, trade_quantity, trade_price, \
            market_capitalization, total_stock = tmp
            
            # save
            trade_date = date
            try: # 중복저장 예방
                sp_data = StockPrice.objects.get(corp_id=corp_id, trade_date=trade_date)
                continue 
            except StockPrice.DoesNotExist:
                sp_data = StockPrice(
                    corp_id=corp_id,
                    trade_date=trade_date,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    total_stock=total_stock,
                    market_capitalization=market_capitalization,
                    trade_quantity=trade_quantity,
                    trade_price=trade_price,
                    change_price=change_price,
                    change_rate=change_rate
                )
                sp_data.save()

        _remove_file(csv_path, operate_system)
        date += timedelta(days=1)

    return fail_list

def collect_stock_price():
    try:
        last_collect_date = LastCollectDate.objects.get()
    except LastCollectDate.DoesNotExist:
        last_collect_date = LastCollectDate()
    
    fail_corp = _collect_new_corps_stocks() # 최초 수집
    fail_date = _collect_stocks(last_date=last_collect_date.last_stock_collect_date) # 마지막 수집일 ~ 오늘 수집
    
    last_collect_date.last_stock_collect_date = datetime.today().date()
    last_collect_date.save()
    
    return fail_corp, fail_date