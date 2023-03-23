"""
@ author : cslee
@ collect fs data
"""
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import time, warnings
import pandas as pd
import numpy as np
import requests
import re
import sys
import os

dir_collect = os.path.dirname(__file__)
dir_modules = os.path.dirname(dir_collect)
dir_admin_dashboard = os.path.dirname(dir_modules)
dir_aimdat = os.path.dirname(dir_admin_dashboard)
sys.path.append(dir_aimdat)

from services.models.corp_id import CorpId
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements
from services.models.stock_price import StockPrice

warnings.filterwarnings('ignore')

def _get_crawl_target_list():

    try:
        crawl_list = CorpId.objects.filter(is_crawl=True)
        ret = []
        for i in crawl_list:
            ret.append(i.stock_code)
        return ret
    except CorpId.DoesNotExist:
        print('크롤링을 해야하는 기업 리스트가 존재하지 않습니다.')

def _make_dart_sector_url(html, sector): 
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

def _crawl_dart(crawl_crp_list, year, month, sleep_time=2):
    # init
    driver = webdriver.Chrome(r'E:\chromedriver_win32\chromedriver.exe') # 윈도우
    months = ['03', '06', '09', '12']
    dict_month = {3:0, 6:1, 9:2, 12:3}
    titles = ['분기보고서', '반기보고서', '분기보고서', '사업보고서']
    dict_title = {month:title for month, title in zip(months, titles)}
    m_idx = dict_month[month]
    month = months[m_idx] # 03
    day = '01'
    # crawl
    ret_fs = []
    for crp_code in crawl_crp_list:
        url = 'https://dart.fss.or.kr/dsab001/main.do'
        driver.get(url)
        time.sleep(sleep_time)
        
        # crp_code
        input_crp = driver.find_element(By.ID, 'textCrpNm')
        input_crp.send_keys(crp_code)
        # startDate
        input_start_date = driver.find_element(By.ID, 'startDate')
        input_start_date.clear()
        start_date = str(year)+month+day
        input_start_date.send_keys(start_date)
        m_idx += 1
        end_year = year + m_idx // 4
        end_month = months[m_idx % 4]
        # endDate
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
        title = dict_title[month]+' 공시뷰어 새창'  # title = '분기보고서 공시뷰어 새창'
        disclosure_date = ''
        for index, value in enumerate(rows):
            body = value.find_element(By.XPATH, "//a[@title='{}']".format(title))
            if body:
                x = value.find_elements(By.TAG_NAME, "td")
                disclosure_date = x[4].text # 접수날짜
                print(disclosure_date)
                break   
        # get df_list
        title = dict_title[month]+' 공시뷰어 새창'  # title = '분기보고서 공시뷰어 새창'
        text_title = driver.find_element(By.XPATH, "//a[@title='{}']".format(title))
        url_rcp = text_title.get_attribute('href')
        response = requests.get(url_rcp)
        time.sleep(sleep_time)
        html = response.text
        url_fs = _make_dart_sector_url(html, '4. 재무제표')
        url_dividend = _make_dart_sector_url(html, '6. 배당에 관한 사항')
        df_fs_list = pd.read_html(url_fs)
        time.sleep(sleep_time)
        df_dividend_list = pd.read_html(url_dividend)
        time.sleep(sleep_time)
   
        ret_fs.append([crp_code, disclosure_date, df_fs_list, df_dividend_list])
    return ret_fs

def _get_stockInfos(corp_id, disclosure_date):
    try:
        sp_data = StockPrice.objects.get(corp_id=corp_id, trade_date=disclosure_date)
        stock_price = sp_data.close_price
        market_captialization = sp_data.market_capitalization
        total_stock = sp_data.total_stock
        return stock_price, market_captialization, total_stock
    except StockPrice.DoesNotExist:
        return None, None, None

def _get_re_word_with_space(word):
        ret = '.*'
        for c in word:
            ret += c
            ret += '\s*'
        ret += '.*'
        return ret

def _parse_fs(df_list):
    
    # init
    table_names = ['재무상태표', '포괄손익계산서', '자본변동표', '현금흐름표']
    units = ['백만원', '원']
    dict_units = {'백만원':1000_000, '원':1}

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
            def crawl_data(keywords):       
                re_keywords = list(map(_get_re_word_with_space, keywords))
                dict_ret = {keyword:None for keyword in keywords}
                for x in df[cols[0]]:
                    for keyword, re_keyword in zip(keywords, re_keywords):
                        tmp = re.findall(re_keyword, str(x))
                        if tmp != []:
                            row = df[ df[cols[0]] == tmp[0]]
                            # 당기
                            val = list(map(float, row[cols[1]].values))
                            total_val = list(map(float, row[cols[2]].values))
                            ret = total_val if np.isnan(val) else val
                            ret = ret[0]
                            if dict_ret[keyword] is None:
                                dict_ret[keyword] = ret * money_unit
                            break
                ret = list(dict_ret.values())
                return ret

            if name[0] =='재': # 재무상태표
                crawl_list = ['자산총계', '부채총계', '자본총계', '차입부채']
                total_asset, total_debt, total_capital, borrow_debt = crawl_data(crawl_list)  
            elif name[0] == '포': # 포괄손익계산서 
                crawl_list = ['영업수익', '영업이익', '기순이익']
                sales_revenue, operate_profit, net_profit = crawl_data(crawl_list)
            break
    
    return total_asset, total_debt, total_capital, borrow_debt, sales_revenue, operate_profit, net_profit

def _parse_dividend(df_list):
    for idx in range(len(df_list)):
        df = df_list[idx]
        cols = df.columns
        re_now = _get_re_word_with_space('당기')
        prev_quarter, now_quarter = '', ''
        for i in range(len(cols)-1):
            col = cols[i]
            x = re.findall(re_now, col)

            if x != []:
                prev_quarter = cols[i+1]
                now_quarter = col # cols[i]
                break
        
        if now_quarter == '': # 상관없는 테이블 건너뛰기
            continue

        def crawl_data(keywords, section):       
            re_keywords = list(map(_get_re_word_with_space, keywords))
            dict_ret = {keyword:None for keyword in keywords}
            for x in df[cols[0]]:
                for keyword, re_keyword in zip(keywords, re_keywords):
                    tmp = re.findall(re_keyword, str(x))
                    if tmp != []:
                        row = df[ df[cols[0]] == tmp[0]]

                        x = str(row[section].values)
                        if re.findall(_get_re_word_with_space('-'), x) != []:
                            continue

                        # 단위
                        unit = ''
                        target = row[cols[0]].values[0]
                        units = ['백만원', '원']
                        for x in units:
                            xx = _get_re_word_with_space(x)
                            y = re.findall(xx, target)
                            if y != []:
                                unit = x
                                break
                        dict_units = {'백만원':1000_000, '원':1, '':1}
                        money_unit = dict_units[unit]
                        # 값
                        ret = list(map(float, row[section].values))[0]
                        if dict_ret[keyword] is None:
                            dict_ret[keyword] = ret * money_unit
                        break
            # print(dict_ret)
            ret = list(dict_ret.values())
            # print(ret)
            return ret

   
        keywords = ['액면가',  '배당금총액', '배당수익률', '배당금']
        # 당기
        face_value, total_dividend, dividend_yield, dividend = crawl_data(keywords, now_quarter)
        # dividend_ratio = dividend / face_value * 100 if dividend is not None & face_value is not None else None
        # 전기
        prev_face_value, prev_total_dividend, prev_dividend_yield, prev_dividend = crawl_data(keywords, prev_quarter)
        # dividend_ratio = dividend / face_value * 100 if dividend is not None & face_value is not None else None
    
    return face_value, total_dividend, dividend_yield, dividend, prev_face_value, prev_total_dividend, prev_dividend_yield, prev_dividend

def _can_calc(a, b):
    return a is not None and b is not None

def _calc_and_update_fs(fs_data:CorpSummaryFinancialStatements, stock_price, market_captialization, total_stock):
    # calculate all params is not None
    if _can_calc(fs_data.operating_profit, fs_data.revenue):
        operate_margin = fs_data.operating_profit / fs_data.revenue * 100
    else:
        operate_margin = None
    if _can_calc(fs_data.net_profit, fs_data.revenue):
        net_profit_margin = fs_data.net_profit / fs_data.revenue * 100
    else:
        net_profit_margin = None
    if _can_calc(fs_data.total_debt, fs_data.total_capital):
        debt_ratio = fs_data.total_debt / fs_data.total_capital * 100
    else:
        debt_ratio = None
    if _can_calc(fs_data.dividend, fs_data.face_value):
        dividend_ratio = fs_data.dividend / fs_data.face_value * 100
    else:
        dividend_ratio = None
    if _can_calc(fs_data.net_profit, total_stock):
        eps = fs_data.net_profit / total_stock
    else:
        eps = None
    if _can_calc(fs_data.total_capital, total_stock):
        bps = fs_data.total_capital / total_stock
    else:
        bps = None
    if _can_calc(fs_data.net_profit, fs_data.total_capital):
        roe = fs_data.net_profit / fs_data.total_capital * 100 # total_captial 이 아닌 평균 자본이 들어가야함
    else:
        roe = None
    if _can_calc(stock_price, fs_data.eps):
        per = stock_price / fs_data.eps
    else:
        per = None
    if _can_calc(stock_price, fs_data.bps):
        pbr = stock_price / fs_data.bps 
    else:
        pbr = None
    if _can_calc(stock_price, market_captialization) and fs_data.revenue is not None:
        psr = stock_price / market_captialization * fs_data.revenue # psr = stock_price / (market_captialization / revenue)
    else:
        psr = None
    if _can_calc(fs_data.total_dividend, total_stock):
        dps = fs_data.total_dividend / total_stock
    else:
        dps = None
    if _can_calc(fs_data.eps, fs_data.dps):
        dividend_payout_ratio = 1 - (fs_data.eps-fs_data.dps)/fs_data.dps
    else:
        dividend_payout_ratio = None
    
    # update value is not None
    if operate_margin is not None:
        fs_data.operating_margin = operate_margin
    if net_profit_margin is not None:
        fs_data.net_profit_margin = net_profit_margin
    if debt_ratio is not None:
        fs_data.debt_ratio = debt_ratio
    if dividend_ratio is not None:
        fs_data.dividend_ratio = dividend_ratio
    if eps is not None:
        fs_data.eps = eps
    if bps is not None:
        fs_data.bps = bps
    if roe is not None:
        fs_data.roe = roe
    if per is not None:
        fs_data.per = per
    if pbr is not None:
        fs_data.pbr = pbr
    if psr is not None:
        fs_data.psr = psr
    if dps is not None:
        fs_data.dps = dps
    if dividend_payout_ratio is not None:
        fs_data.dividend_payout_ratio = dividend_payout_ratio
    fs_data.save()

def collect_fs_data(year, month):
    crawl_list = _get_crawl_target_list()
    ret = _crawl_dart(crawl_list, year, month, sleep_time=2) # [crp_code, disclosure_date, df_fs_list, df_dividend_list]
    # calc and save
    for crp_code, disclosure_date, df_fs_list, df_dividend_list in ret:
       
        # parse_fs
        total_asset, total_debt, total_capital, borrow_debt, sales_revenue, operate_profit, net_profit = _parse_fs(df_fs_list)
        # parse_dividend
        face_value, total_dividend, dividend_yield, dividend, prev_face_value, prev_total_dividend, prev_dividend_yield, prev_dividend = _parse_dividend(df_dividend_list)

        # save  
        try:
            corp_id = CorpId.objects.get(stock_code=crp_code)
        except CorpId.DoesNotExist:
            continue
        
        try:
            fs_data = CorpSummaryFinancialStatements.objects.get(corp_id=corp_id, year=year, month=month)
            fs_data.disclosure_date = disclosure_date
            fs_data.revenue=sales_revenue
            fs_data.operating_profit=operate_profit
            fs_data.net_profit=net_profit
            fs_data.face_value=face_value
            fs_data.dividend=dividend
            fs_data.total_dividend=total_dividend
            fs_data.dividend_yield=dividend_yield
            fs_data.total_asset=total_asset
            fs_data.total_debt=total_debt
            fs_data.total_capital=total_capital
            fs_data.borrow_debt=borrow_debt
        except CorpSummaryFinancialStatements.DoesNotExist:
            fs_data = CorpSummaryFinancialStatements(  # create
                corp_id=corp_id,
                disclosure_date=disclosure_date,
                year=year,
                month=month,
                revenue=sales_revenue,
                operating_profit=operate_profit,
                net_profit=net_profit,
                face_value=face_value,
                dividend=dividend,
                total_dividend=total_dividend,
                dividend_yield=dividend_yield,
                total_asset=total_asset,
                total_debt=total_debt,
                total_capital=total_capital,
                borrow_debt=borrow_debt,
            )
        fs_data.save()

        # DB disclosure_date ( open data에서 stockprice 수집이 선행되어야함)
        stock_price, market_captialization, total_stock = _get_stockInfos(corp_id, disclosure_date)
        _calc_and_update_fs(fs_data, stock_price, market_captialization, total_stock)
      

        # 전기 배당정보 update
        # calc year and month
        prev_month = (month + 9) % 12
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        try:
            fs_prev_data = CorpSummaryFinancialStatements.objects.get(corp_id=corp_id, year=prev_year, month=prev_month)
            fs_prev_data.face_value=prev_face_value
            fs_prev_data.dividend=prev_dividend
            fs_prev_data.total_dividend=prev_total_dividend
            fs_prev_data.dividend_yield=prev_dividend_yield
        except CorpSummaryFinancialStatements.DoesNotExist:
            fs_prev_data = CorpSummaryFinancialStatements(  # create
                corp_id=corp_id,
                year=prev_year,
                month=prev_month,
                face_value=prev_face_value,
                dividend=prev_dividend,
                total_dividend=prev_total_dividend,
                dividend_yield=prev_dividend_yield
            )
        fs_prev_data.save()

        prev_disclosure_date = fs_prev_data.disclosure_date
        prev_stock_price, prev_market_captialization, prev_total_stock = _get_stockInfos(corp_id, prev_disclosure_date)
        _calc_and_update_fs(fs_prev_data, prev_stock_price, prev_market_captialization, prev_total_stock)
