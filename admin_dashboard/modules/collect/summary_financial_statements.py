"""
@created at 2023.04.14
@author cslee in Aimdat Team
"""
import numpy as np
import os
import pandas as pd
import re
import requests
import sys
import time
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
dir_collect = os.path.dirname(__file__)
dir_modules = os.path.dirname(dir_collect)
dir_admin_dashboard = os.path.dirname(dir_modules)
dir_aimdat = os.path.dirname(dir_admin_dashboard)
sys.path.append(dir_aimdat)
from admin_dashboard.models.last_collect_date import LastCollectDate
from services.models.corp_id import CorpId
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements
from services.models.stock_price import StockPrice

units = ['백만원', '원']
dict_units = {'백만원':1000_000, '원':1, '':1}

def _get_corp_list():
    try:
        corp_list = CorpId.objects.all()
        stock_code_list = [i.stock_code for i in corp_list]
        return stock_code_list
    except CorpId.DoesNotExist:
        return []

def _get_url_dart_sector(html, sector): 
    x = html.split(sector)[1]
    x = x.split('rcpNo')[1]
    rcpNo = x.split('"')[1]
    x = x.split('dcmNo')[1]
    dcmNo = x.split('"')[1]
    x = x.split('eleId')[1]
    eleId = x.split('"')[1]
    x = x.split('offset')[1]
    offset = x.split('"')[1]
    x = x.split('length')[1]
    length = x.split('"')[1]

    url = 'http://dart.fss.or.kr/report/viewer.do?rcpNo=' + str(rcpNo) + '&dcmNo=' + str(dcmNo) + '&eleId=' + str(eleId) + '&offset=' + str(offset) +'&length=' + str(length) + '&dtd=dart3.xsd'
    return url

def _crawl_dart(crawl_crp_list, year:int, quarter:int, sleep_time=2):
    # init
    driver = webdriver.Chrome(ChromeDriverManager().install())
    months = {1:'03', 2:'06', 3:'09', 4:'12'}
    titles = {1:'분기보고서', 2:'반기보고서', 3:'분기보고서', 4:'사업보고서'}
    month = months[quarter]
    day = '01'
    logs = []
    # crawl
    crawl_result = []
    for stock_code in crawl_crp_list:
        url = 'https://dart.fss.or.kr/dsab001/main.do'
        driver.get(url)
        time.sleep(sleep_time)
        
        # crp_code
        input_crp = driver.find_element(By.ID, 'textCrpNm')
        input_crp.send_keys(stock_code)
        # startDate
        input_start_date = driver.find_element(By.ID, 'startDate')
        input_start_date.clear()
        start_date = str(year)+month+day
        input_start_date.send_keys(start_date)
        # endDate
        end_quarter = quarter % 4 + 1
        end_year = year + (end_quarter == 1)
        end_month = months[end_quarter]
        input_end_date = driver.find_element(By.ID, 'endDate')
        input_end_date.clear()
        end_date = str(end_year)+end_month+day
        input_end_date.send_keys(end_date)
        # checkbox
        checkbox_finance = driver.find_element(By.XPATH, '//img[@alt="정기공시 선택"]')
        checkbox_finance.click()
        # btn_search
        btn_search = driver.find_element(By.CLASS_NAME, 'btnSearch')
        btn_search.click()
        time.sleep(sleep_time)
        # get disclosure_date
        table = driver.find_element(By.CLASS_NAME, "tbList")
        tbody = table.find_element(By.ID, "tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")    
        title = titles[quarter]+' 공시뷰어 새창'  # title = '분기보고서 공시뷰어 새창'
        disclosure_date = ''

        body = None
        for value in rows:
            try:
                body = value.find_element(By.XPATH, "//a[@title='{}']".format(title))
            except NoSuchElementException:
                continue

            try:
                x = value.find_elements(By.TAG_NAME, "td")
                disclosure_date = x[4].text # 접수날짜
            except NoSuchElementException:
                disclosure_date = None
                logs.append([stock_code, 'NOT_DISCLOSURE_DATE'])
            break  
        
        if body == None:
            logs.append([stock_code, 'NOT_REPORT'])
            continue

        # get df_list
        text_title = driver.find_element(By.XPATH, "//a[@title='{}']".format(title))
        url_rcp = text_title.get_attribute('href')
        response = requests.get(url_rcp)
        time.sleep(sleep_time)
        html = response.text
        url_fs = _get_url_dart_sector(html, '4. 재무제표')
        url_dividend = _get_url_dart_sector(html, '6. 배당에 관한 사항')
        df_fs_list = pd.read_html(url_fs)
        time.sleep(sleep_time)
        df_dividend_list = pd.read_html(url_dividend)
        time.sleep(sleep_time)
   
        disclosure_date = None if disclosure_date == '' else disclosure_date
   
        crawl_result.append([stock_code, disclosure_date, df_fs_list, df_dividend_list])
    return crawl_result, logs

def _get_stock_data(corp_id, disclosure_date):
    if disclosure_date == None:
        return None, None, None
    
    try:
        sp_data = StockPrice.objects.get(corp_id=corp_id, trade_date=disclosure_date)
        stock_price = sp_data.close_price # 공시일의 종가를 주가로 사용
        market_captialization = sp_data.market_capitalization
        total_stock = sp_data.total_stock
        return stock_price, market_captialization, total_stock
    except StockPrice.DoesNotExist:
        return None, None, None

def _get_re_word_with_space(word):
        return '.*' + '\s*'.join(word) + '.*'

## 파싱 둘자 전체적으로 리팩토링 ㄱ ㄱ
def _parse_fs(df_list):
    names = ['total_asset', 'total_debt', 'total_capital', 'borrow_debt', 'revenue', 'operate_profit', 'net_profit', 'sale_revenue']
    result = { key:None for key in names}

    def crawl_data(keywords):       
        re_keywords = list(map(_get_re_word_with_space, keywords))
        result = {keyword:None for keyword in keywords}
        for x in df[cols[0]]:
            for keyword, re_keyword in zip(keywords, re_keywords):
                tmp = re.findall(re_keyword, str(x))
                if tmp == []:
                    continue
                
                row = df[ df[cols[0]] == tmp[0]]
                # 당기
                value = list(map(float, row[cols[1]].values))
                total_value = list(map(float, row[cols[2]].values))

                total_value = total_value if np.isnan(value) else value
                total_value = total_value[0]

                if result[keyword] is None: # 나중에 로직 수정이 필요한 부분 # none일때만 수집
                    result[keyword] = total_value * money_unit
                break
        result = list(result.values())
        return result

    # init
    table_names = ['재무상태표', '포괄손익계산서', '자본변동표', '현금흐름표']
    for idx in range(len(df_list)-1):
        df = df_list[idx]
        cols = df.columns
        table_text = df[cols[0]][0]
        for name in table_names:
            # 테이블 크롤
            re_name = _get_re_word_with_space(name)
            tmp = re.findall(re_name, table_text)
            if tmp == []: 
                continue
            # 단위 부분 크롤
            re_unit = _get_re_word_with_space('단위')          
            unit = ''    
            for col in cols:
                for x in df[col]:
                    y = re.findall(re_unit, x)
                    if y != []:
                        unit = y[0]
                        break
            # 정확한 단위 크롤
            for x in units:
                xx = _get_re_word_with_space(x)
                y = re.findall(xx, unit)
                if y != []:
                    unit = x
                    break
            money_unit = dict_units[unit]
            # data_table
            df = df_list[idx+1]
            cols = df.columns

            if name[0] =='재': # 재무상태표
                crawl_list = ['자산총계', '부채총계', '자본총계', '차입부채']
                result['total_asset'], result['total_dept'], result['total_capital'], result['borrow_debt'] = crawl_data(crawl_list)  

            elif name[0] == '포': # 포괄손익계산서 
                crawl_list = ['매출액', '영업이익', '기순이익', '영업수익']
                result['revenue'], result['operate_profit'], result['net_profit'], result['sale_revenue'] = crawl_data(crawl_list)

    return result

def _parse_dividend(df_list):  
    names = ['face_value', 'total_dividend', 'dividend_yield', 'dividend']
    result = { key:None for key in names}

    def crawl_data(keywords, section):       
        re_keywords = list(map(_get_re_word_with_space, keywords))
        dict_ret = {keyword:None for keyword in keywords}
        for x in df[cols[0]]:
            for keyword, re_keyword in zip(keywords, re_keywords):
                tmp = re.findall(re_keyword, str(x))
                if tmp == []:
                    continue
                row = df[df[cols[0]] == tmp[0]]
                x = str(row[section].values)
                if re.findall(_get_re_word_with_space('-'), x) != []:
                    continue
                # 단위
                unit = ''
                target = row[cols[0]].values[0]       
                for x in units:
                    xx = _get_re_word_with_space(x)
                    y = re.findall(xx, target)
                    if y != []:
                        unit = x
                        break
                money_unit = dict_units[unit]
                # 값 계산
                ret = list(map(float, row[section].values))[0]
                if dict_ret[keyword] is None:
                    dict_ret[keyword] = ret * money_unit
                break 
        ret = list(dict_ret.values())
        return ret
    # main
    for idx in range(len(df_list)):
        df = df_list[idx]
        cols = df.columns
        re_now = _get_re_word_with_space('당기')
        now_quarter = ''
        for i in range(len(cols)-1):
            col = cols[i]
            x = re.findall(re_now, col)
            if x != []:
                now_quarter = col # cols[i]
                break
        if now_quarter == '': # 상관없는 테이블 건너뛰기
            continue

        keywords = ['액면가',  '배당금총액', '배당수익률', '배당금']    
        result['face_value'], result['total_dividend'], result['dividend_yield'], result['dividend'] = crawl_data(keywords, now_quarter)
        break
    
    return result

def _can_calc(a=0, b=0, c=0):
    return a is not None and b is not None and c is not None

# decimal, float 정리
def _calc_and_update_fs(fs_data:CorpSummaryFinancialStatements, stock_price, market_captialization, total_stock):
    # Decimal to float
    stock_price = float(stock_price) if stock_price is not None else None
    market_captialization = float(stock_price) if market_captialization is not None else None
    total_stock = float(stock_price) if total_stock is not None else None
    operating_profit = float(fs_data.operating_profit) if fs_data.operating_profit is not None else None
    revenue = float(fs_data.revenue) if fs_data.revenue is not None else None
    net_profit = float(fs_data.net_profit) if fs_data.net_profit is not None else None
    dividend = float(fs_data.dividend ) if fs_data.dividend is not None else None
    face_value = float(fs_data.face_value) if fs_data.face_value is not None else None
    total_debt = float(fs_data.total_debt) if fs_data.total_debt is not None else None
    total_capital = float(fs_data.total_capital) if fs_data.total_capital is not None else None
    total_dividend = float(fs_data.total_dividend) if fs_data.total_dividend is not None else None
    dps = float(fs_data.dps) if fs_data.dps is not None else None

    operate_margin = operating_profit / revenue * 100 if _can_calc(operating_profit, revenue) else None
    net_profit_margin = net_profit / revenue * 100 if _can_calc(net_profit, revenue) else None
    debt_ratio = total_debt / total_capital * 100 if _can_calc(total_debt, total_capital) else None
    dividend_ratio = dividend / face_value * 100 if _can_calc(dividend, face_value) else None
    eps = net_profit / total_stock if _can_calc(net_profit, total_stock) else None
    bps = total_capital / total_stock if _can_calc(total_capital, total_stock) else None
    # roe 평균자본이 사용되어야함
    roe = net_profit / total_capital * 100 if _can_calc(net_profit, total_capital) else None
    per = stock_price / eps if _can_calc(stock_price, eps) else None
    pbr = stock_price / bps  if _can_calc(stock_price, bps) else None
    # psr = stock_price / (market_captialization / revenue)
    psr = stock_price / market_captialization * revenue if _can_calc(stock_price, market_captialization, revenue) else None
    dps = total_dividend / total_stock if _can_calc(total_dividend, total_stock) else None
    dividend_payout_ratio = 1 - (eps-dps)/dps if _can_calc(eps, dps) else None
    
    # update when value is not None
    if _can_calc(operate_margin):
        fs_data.operating_margin = operate_margin
    if _can_calc(net_profit_margin):
        fs_data.net_profit_margin = net_profit_margin
    if _can_calc(debt_ratio):
        fs_data.debt_ratio = debt_ratio
    if _can_calc(dividend_ratio):
        fs_data.dividend_ratio = dividend_ratio
    if _can_calc(eps):
        fs_data.eps = eps
    if _can_calc(bps):
        fs_data.bps = bps
    if _can_calc(roe):
        fs_data.roe = roe
    if _can_calc(per):
        fs_data.per = per
    if _can_calc(pbr):
        fs_data.pbr = pbr
    if _can_calc(psr):
        fs_data.psr = psr
    if _can_calc(dps):
        fs_data.dps = dps
    if _can_calc(dividend_payout_ratio):
        fs_data.dividend_payout_ratio = dividend_payout_ratio
    fs_data.save()

def collect_summary_finaicial_statements(year:int, quarter:int):
    logs = []
    corp_list = _get_corp_list()
    crawl_result, logs_crawl = _crawl_dart(corp_list, year, quarter, sleep_time=2) # [stock_code, disclosure_date, df_fs_list, df_dividend_list]
    logs += logs_crawl

    for stock_code, disclosure_date, df_fs_list, df_dividend_list in crawl_result:
        try:
            corp_id = CorpId.objects.get(stock_code=stock_code)
        except CorpId.DoesNotExist: # 존재하지 않는 stock_code # not fail
            continue  
        # # 재무제표 
        # parse
        if disclosure_date is not None:
            yy, mm, dd = disclosure_date.split('.')
            disclosure_date = datetime(int(yy), int(mm), int(dd)).date()

        result_fs = _parse_fs(df_fs_list)
        # logging
        for name, value in result_fs.items():
            if value is not None:
                continue
            logs.append([stock_code, 'NOT_'+name])

        revenue, operate_profit, net_profit, total_asset, total_debt, total_capital, borrow_debt = \
        result_fs['revenue'], result_fs['operate_profit'], result_fs['net_profit'], result_fs['total_asset'], result_fs['total_debt'], result_fs['total_capital'], result_fs['borrow_debt']
        # save  
        try:
            fs_data = CorpSummaryFinancialStatements.objects.get(corp_id=corp_id, year=year, quarter=quarter)
            fs_data.disclosure_date = disclosure_date
            fs_data.revenue=revenue
            fs_data.operating_profit=operate_profit
            fs_data.net_profit=net_profit
            fs_data.total_asset=total_asset
            fs_data.total_debt=total_debt
            fs_data.total_capital=total_capital
            fs_data.borrow_debt=borrow_debt
        except CorpSummaryFinancialStatements.DoesNotExist:
            fs_data = CorpSummaryFinancialStatements(  # create
                corp_id=corp_id,
                disclosure_date=disclosure_date,
                year=year,
                quarter=quarter,
                revenue=revenue,
                operating_profit=operate_profit,
                net_profit=net_profit,
                total_asset=total_asset,
                total_debt=total_debt,
                total_capital=total_capital,
                borrow_debt=borrow_debt,
            )
        fs_data.save()
        # calculate data
        stock_price, market_captialization, total_stock = _get_stock_data(corp_id, disclosure_date)
        _calc_and_update_fs(fs_data, stock_price, market_captialization, total_stock)
        
        if quarter != 4: # 사업보고서만 배당부분을 크롤한다
            continue
        # # 배당
        # parse
        result_dividend = _parse_dividend(df_dividend_list)
        # logging
        for name, value in result_dividend.items():
            if value is not None:
                continue
            logs.append([stock_code, 'NOT_'+name])

        face_value, total_dividend, dividend_yield, dividend = \
        result_dividend['face_value'], result_dividend['total_dividend'], result_dividend['dividend_yield'], result_dividend['dividend']
        # save
        for q in [1,2,3,4]:
            try:
                fs_data = CorpSummaryFinancialStatements.objects.get(corp_id=corp_id, year=year, quarter=q)
                fs_data.face_value=face_value
                fs_data.dividend=dividend
                fs_data.total_dividend=total_dividend
                fs_data.dividend_yield=dividend_yield
                fs_data.save()
            except CorpSummaryFinancialStatements.DoesNotExist: # 해당분기의 재무제표가 원래 존재하지 않음
                continue

            disclosure_date = fs_data.disclosure_date
            stock_price, market_captialization, total_stock = _get_stock_data(corp_id, disclosure_date)
            _calc_and_update_fs(fs_data, stock_price, market_captialization, total_stock)
    
    # 마지막 수집일 갱신    
    try:
        last_collect_date = LastCollectDate.objects.get()
    except LastCollectDate.DoesNotExist:
        last_collect_date = LastCollectDate()
    
    last_collect_date.last_summaryfs_collect_date = datetime.today()
    last_collect_date.save()

    return logs