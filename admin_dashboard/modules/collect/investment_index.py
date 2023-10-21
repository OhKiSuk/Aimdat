"""
@created at 2023.05.10
@author JSU in Aimdat Team

@modified at 2023.10.16
@author OKS in Aimdat Team
"""
import logging
import os
import zipfile
import pymongo
import re
import requests
import time
import xml.etree.ElementTree as ET

from admin_dashboard.modules.api_error.open_dart_api_error import check_open_dart_api_error
from admin_dashboard.modules.remove.remove_files import remove_files
from config.settings.base import (
    get_secret,
    BASE_DIR
)
from decimal import (
    Context,
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP
)
from django.db.models import (
    DateField,
    F,
    Q
)
from django.db.models.functions import Cast
from requests import ConnectionError, ConnectTimeout, Timeout, RequestException
from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice
from services.models.investment_index import InvestmentIndex

DOWNLOAD_PATH = get_secret('download_folder')

# 계정과목 목록
ACCOUNTS_PATH = os.path.join(BASE_DIR, 'account_list')

LOGGER = logging.getLogger(__name__)

def _download_corp_code():
    """
    Opendart의 고유번호 파일 다운로드
    """
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    params = {
        'crtfc_key': get_secret('crtfc_key') 
    }
    # A003 로깅
    try:
        response = requests.get(url, params=params)
    
        with open(os.path.join(DOWNLOAD_PATH, 'corpCode.zip'), 'wb') as file:
            file.write(response.content)
    except:
        LOGGER.error('[A003] CORPCODE 다운로드 실패.')

def _unzip_corp_code():
    """
    Opendart의 고유번호 파일 압축해제
    """

    # A004 로깅
    try:
        with zipfile.ZipFile(os.path.join(DOWNLOAD_PATH, 'corpCode.zip'), 'r') as zip_file:
            zip_file.extract('CORPCODE.xml', DOWNLOAD_PATH)
    except:
        LOGGER.error('[A004] CORPCODE 압축 해제 실패.')

def _get_collect_corp_list(stock_codes, year, quarter):
    """
    해당 년도에 재무제표가 존재하는 기업의 종목코드 목록 생성
    """
    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements']

    corp_list = []
    for stock_code in stock_codes:
        query = {'년도': year, '분기': quarter, '종목코드': stock_code}

        if collection.count_documents(query) > 0:
            corp_list.append(stock_code)

    return corp_list

def _parse_investment_index(year, quarter, fs_type, corp_list):
    """
    기업 데이터 파싱 후 투자지표 데이터로 변환
    """
    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements']

    # 숫자 아닌 값 확인
    not_digit_pattern = re.compile(r'\D')

    # 재무제표 타입 {연결: 0, 별도: 5}
    if fs_type == '0':
        fs_type_regex = '연결'
    elif fs_type == '5':
        fs_type_regex = '별도'

    # 계정과목 목록 가져오기
    bs_list = ['매입채무', '매출채권', '부채총계', '유동부채', '유동자산', '자본총계', '자산총계', '재고자산', '현금성자산']
    pl_list = ['당기순이익', '매출액', '매출원가', '법인세비용', '영업이익', '이자비용']
    cf_list = ['감가상각비', '영업활동', '재무활동', '투자활동']

    file_list = os.listdir(ACCOUNTS_PATH)
    account_dict = {}

    for file_name in file_list:
        file_path = os.path.join(ACCOUNTS_PATH, file_name)
        account_list = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                account_list.append(line.replace('\n', ''))

            account_dict[os.path.splitext(file_name)[0]] = account_list

    # 나눗셈 정확도 설정
    ctx = Context(prec=6)

    # 전기 년도, 분기 확인
    if quarter == 2:
        before_quarter = 1
        before_year = year
    elif quarter == 3:
        before_quarter = 2
        before_year = year
    elif quarter == 4:
        before_quarter = 3
        before_year = year
    else:
        before_quarter = quarter
        before_year = year

    # 데이터 수집
    index_list = []
    for stock_code in corp_list:

        # 당해 재무제표가 존재하는 지 확인(없으면 생략)
        if collection.count_documents({'종목코드': stock_code, '년도': year, '분기': quarter, '재무제표종류': {'$regex': fs_type_regex+'재무상태표'}}) < 1:
            continue

        # 단위 설정
        set_unit = Decimal('100_000_000')

        # 변수 초기화
        trade_payables = Decimal('0')
        trade_receivables = Decimal('0')
        total_debt = Decimal('0')
        current_debt = Decimal('0')
        current_assets = Decimal('0')
        total_capital = Decimal('0')
        total_assets = Decimal('0')
        inventory = Decimal('0')
        cash_equivalents = Decimal('0')
        net_profit = Decimal('0')
        revenue = Decimal('0')
        operating_profit = Decimal('0')
        cost_of_sales = Decimal('0')
        interest_expense = Decimal('0')
        corporate_tax = Decimal('0')
        depreciation = Decimal('0')
        operating_cash_flow = Decimal('0')
        financing_cash_flow = Decimal('0')
        investing_cash_flow = Decimal('0')
        dps = Decimal('0')
        total_dividend = Decimal('0')
        dividend_payout_ratio = Decimal('0')
        dividend_ratio = Decimal('0')
        before_revenue = Decimal('0')
        before_total_assets = Decimal('0')
        before_total_capital = Decimal('0')
        before_operating_profit = Decimal('0')
        before_net_profit = Decimal('0')
        before_dividend = Decimal('0')
        before_dps = Decimal('0')
        value = Decimal('0')
        before_value = Decimal('0')
        now_value = Decimal('0')

        # StockPrice 값 연결
        if StockPrice.objects.annotate(date_field=Cast(F('trade_date'), output_field=DateField())).filter(Q(corp_id__stock_code__exact = stock_code) & Q(date_field__year__exact = year) & Q(date_field__month__exact = quarter * 3)).exists():
            stock_price_obj = StockPrice.objects.annotate(date_field=Cast(F('trade_date'), output_field=DateField())).filter(Q(corp_id__stock_code__exact = stock_code) & Q(date_field__year__exact = year) & Q(date_field__month__exact = quarter * 3)).latest('date_field')
            market_capitalization = ctx.divide(stock_price_obj.market_capitalization, set_unit) # 시가총액
            shares_outstanding = stock_price_obj.total_stock # 발행주식수
        else:
            # A603 로깅
            LOGGER.info('[A603] 저장된 주가 정보가 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
            market_capitalization = 0
            shares_outstanding = 0

        for account_category, account_list in account_dict.items():
            if account_category in bs_list:
                query = {'종목코드': stock_code, '년도': year, '분기': quarter, '재무제표종류': {'$regex': fs_type_regex+'재무상태표'}}
                before_query = {'종목코드': stock_code, '년도': before_year, '분기': before_quarter, '재무제표종류': {'$regex': fs_type_regex+'재무상태표'}}
            elif account_category in pl_list:
                query = {'종목코드': stock_code, '년도': year, '분기': quarter, '재무제표종류': {'$regex': fs_type_regex+'(포괄)?손익계산서'}}
                before_query = {'종목코드': stock_code, '년도': before_year, '분기': before_quarter, '재무제표종류': {'$regex': fs_type_regex+'(포괄)?손익계산서'}}
            elif account_category in cf_list:
                query = {'종목코드': stock_code, '년도': year, '분기': quarter, '재무제표종류': {'$regex': fs_type_regex+'현금흐름표'}}
                before_query = {'종목코드': stock_code, '년도': before_year, '분기': before_quarter, '재무제표종류': {'$regex': fs_type_regex+'현금흐름표'}}

            documents = collection.find(query)

            for document in documents:
                # 단위 설정
                if document['단위'] == '천원':
                    set_unit = Decimal('100_000')
                elif document['단위'] == '백만원':
                    set_unit = Decimal('100')
                
                for key in list(document.keys()):
                        
                    if str(key).strip() in account_list:

                        if account_category in bs_list or account_category in cf_list:
                            value = _check_is_nan(ctx.divide(Decimal(str(document[key].to_decimal())), set_unit))

                            # 재무상태표 값 초기화
                            if account_category == '매입채무':
                                trade_payables = value
                            elif account_category == '매출채권':
                                trade_receivables = value
                            elif account_category == '부채총계':
                                total_debt = value
                            elif account_category == '유동부채':
                                current_debt = value
                            elif account_category == '유동자산':
                                current_assets = value
                            elif account_category == '자산총계':
                                total_assets = value
                            elif account_category == '재고자산':
                                inventory = value
                            elif account_category == '현금성자산':
                                cash_equivalents = value
                            # 현금흐름표 값
                            elif account_category == '감가상각비':
                                depreciation = value
                            elif account_category == '영업활동':
                                operating_cash_flow = value
                            elif account_category == '재무활동':
                                financing_cash_flow = value
                            elif account_category == '투자활동':
                                investing_cash_flow = value

                        elif account_category in pl_list:

                            is_financial_industry = CorpId.objects.get(stock_code=stock_code).is_financial_industry
                            
                            # 금융업(누적 수치 사용하지 않음) 및 1분기일 경우 수치 즉시 저장
                            if quarter == 1 or is_financial_industry:
                                value = _check_is_nan(ctx.divide(Decimal(str(document[key].to_decimal())), set_unit))
                            else:
                                # 당분기 수치(누적분)
                                now_value = _check_is_nan(ctx.divide(Decimal(str(document[key].to_decimal())), set_unit))

                                # 전기 데이터 조회
                                before_documents = collection.find(before_query)

                                for before_document in before_documents:
                                    for before_key in before_document:
                                        if str(before_key).strip() in account_list:
                                            # 전기 수치
                                            before_value = _check_is_nan(ctx.divide(Decimal(str(before_document[before_key].to_decimal())), set_unit))
                                            value = now_value - before_value

                            # 손익계산서 값
                            if account_category == '당기순이익':
                                net_profit = value
                            elif account_category == '매출액':
                                revenue = value
                            elif account_category == '영업이익':
                                operating_profit = value
                            elif account_category == '매출원가':
                                cost_of_sales = value
                            elif account_category == '이자비용':
                                interest_expense = value
                            elif account_category == '법인세비용':
                                corporate_tax = value

        # 성장률 계산에 필요한 전기 데이터 조회(2020년 1분기 이전 데이터는 가져오지 않음)
        if quarter != 1:
            before_data = InvestmentIndex.objects.filter(corp_id__stock_code=stock_code, year=str(before_year), quarter=str(before_quarter), fs_type=str(fs_type)). \
                only('revenue', 'operating_profit', 'net_profit', 'total_capital', 'total_assets', 'dps')
        else:
            before_data = []

        if before_data:
            for data in before_data:
                before_revenue = data.revenue
                before_total_assets = data.total_assets
                before_total_capital = data.total_capital
                before_operating_profit = data.operating_profit
                before_net_profit = data.net_profit
                before_dps = data.dps
                before_dividend = data.dividend

        # Opendart에서 배당데이터 수집
        url = 'https://opendart.fss.or.kr/api/alotMatter.xml'

        # XML 파일 트리 생성
        corp_code_tree = ET.parse(os.path.join(DOWNLOAD_PATH, 'CORPCODE.xml'))
        corp_code_root = corp_code_tree.getroot()

        # corp_code 확인
        for element in corp_code_root.iter('list'):
            stock_code_element = element.find('stock_code').text

            if str(stock_code_element) == str(stock_code):
                corp_code = str(element.find('corp_code').text).zfill(8)
        
                # 분기 기반 보고서 데이터 생성
                if quarter == 4:
                    reprt_code = 11011
                elif quarter == 3:
                    reprt_code = 11014
                elif quarter == 2:
                    reprt_code = 11012
                elif quarter == 1:
                    reprt_code = 11013

                params = {
                    'crtfc_key': get_secret('crtfc_key'), 
                    'corp_code': corp_code, 
                    'bsns_year': year, 
                    'reprt_code': reprt_code
                }

                # API 호출 로깅
                try:
                    response = requests.get(url, params=params)
                except ConnectTimeout:
                    LOGGER.error('[A013] Requests 연결 타임아웃 에러. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                except ConnectionError:
                    LOGGER.error('[A012] Requests 연결 에러. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                except Timeout:
                    LOGGER.error('[A011] Requests 타임아웃 에러. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                except RequestException:
                    LOGGER.error('[A010] Requests 범용 에러. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))

                time.sleep(0.3)
                # OPENDART_API_ERROR 로깅
                check_open_dart_api_error(response)

                if response.status_code == 200:
                    # 반환데이터 트리 생성
                    xml_data = response.text
                    api_root = ET.fromstring(xml_data)

                    for element in api_root.iter('list'):
                        
                        # 보통주 배당금 수집
                        if re.match(r'주당 현금배당금', element.find('se').text):
                            if element.find('stock_knd') != r'우선주':
                                try:
                                    value = not_digit_pattern.sub('', element.find('thstrm').text)

                                    if value:
                                        dps_value = Decimal(value).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                                        if quarter == 1:
                                            dps = dps_value
                                        else:
                                            dps = dps_value - before_dps

                                    # 당기에 배당을 안했을 경우
                                    if dps < Decimal('0'):
                                        dps = Decimal('0')
                                except:
                                    LOGGER.info('[A604] 배당정보 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                                    dps = Decimal('0')
                        # 현금 배당금 총액 수집
                        elif re.match(r'현금배당금총액', element.find('se').text):
                            if element.find('stock_knd') != r'우선주':
                                try:
                                    value = not_digit_pattern.sub('', element.find('thstrm').text)
                                    if value:
                                        total_dividend_value = ctx.multiply(Decimal(value), Decimal('1_000_000')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                                        if quarter == 1:
                                            total_dividend = total_dividend_value
                                        else:
                                            total_dividend = total_dividend_value - ctx.multiply(before_dividend, Decimal('100_000_000'))
                                    
                                    if total_dividend < Decimal('0'):
                                        total_dividend = Decimal('0')
                                except:
                                    LOGGER.info('[A604] 배당정보 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                                    total_dividend = Decimal('0')
                        # 현금배당성향 수집
                        elif re.match(r'.*현금배당성향', element.find('se').text):
                            if element.find('stock_knd') != r'우선주':
                                try:
                                    value = element.find('thstrm').text
                                    if value != '-':
                                        dividend_payout_ratio = Decimal(value)
                                    
                                    if dividend_payout_ratio < Decimal('0'):
                                        dividend_payout_ratio = Decimal('0')
                                except:
                                    LOGGER.info('[A604] 배당정보 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                                    dividend_payout_ratio = Decimal('0')
                        # 현금배당수익률 수집
                        elif re.match(r'현금배당수익률', element.find('se').text):
                            if element.find('stock_knd') != r'우선주':
                                try:
                                    value = element.find('thstrm').text
                                    if value != '-':
                                        dividend_ratio = Decimal(value)
                                    
                                    if dividend_ratio < Decimal('0'):
                                        dividend_ratio = Decimal('0')
                                except:
                                    LOGGER.info('[A604] 배당정보 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                                    dividend_ratio = Decimal('0')
                """
                자본 총계 계산
                """                
                try:
                    total_capital = total_assets - total_debt
                except (InvalidOperation, ZeroDivisionError):
                    current_ratio = Decimal('0')

                """
                안정성 지표

                유동비율, 당좌비율, 부채비율, 이자보상비율
                """
                try:
                    current_ratio = _check_is_nan(ctx.divide(current_assets, current_debt) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    current_ratio = Decimal('0')

                try:
                    quick_ratio = _check_is_nan(ctx.divide((current_assets-inventory), current_debt) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    quick_ratio = Decimal('0')

                try:
                    debt_ratio = _check_is_nan(ctx.divide(total_debt, total_capital) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    debt_ratio = Decimal('0')

                try:
                    interest_coverage_ratio = _check_is_nan(ctx.divide(operating_profit, interest_expense)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    interest_coverage_ratio = Decimal('0')

                """
                수익성 지표

                매출원가율, 매출총이익률, 영업이익률, 순이익률, 총자본영업이익률, 자기자본이익률, 총자산순이익률
                """
                try:
                    cost_of_sales_ratio = _check_is_nan(ctx.divide(cost_of_sales, revenue) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    cost_of_sales_ratio = Decimal('0')

                try:
                    gross_profit_margin = _check_is_nan(ctx.divide((revenue-cost_of_sales), revenue) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    gross_profit_margin = Decimal('0')

                try:
                    operating_margin = _check_is_nan(ctx.divide(operating_profit, revenue) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    operating_margin = Decimal('0')

                try:
                    net_profit_margin = _check_is_nan(ctx.divide(net_profit, revenue) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    net_profit_margin = Decimal('0')

                try:
                    roic = _check_is_nan(ctx.divide(operating_profit, total_capital) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    roic = Decimal('0')

                try:
                    roe = _check_is_nan(ctx.divide(net_profit, total_capital) * Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    roe = Decimal('0')

                try:
                    roa = _check_is_nan(ctx.multiply(ctx.divide(net_profit, total_assets), Decimal('100')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    roa = Decimal('0')

                """
                활동성

                총자산회전율, 재고자산회전율, 매출채구너회전율, 매입채무회전율, 운전자본소요율(일), 1회 운전자본
                """
                try:
                    total_assets_turnover = _check_is_nan((ctx.divide(revenue, total_capital)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    total_assets_turnover = Decimal('0')
                
                try:
                    inventory_turnover = _check_is_nan(ctx.divide(revenue, inventory).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    inventory_turnover = Decimal('0')

                try:
                    accounts_receivables_turnover = _check_is_nan(ctx.divide(revenue, trade_receivables).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    accounts_receivables_turnover = Decimal('0')

                try:
                    accounts_payable_turnover = _check_is_nan(ctx.divide(revenue, trade_payables).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    accounts_payable_turnover = Decimal('0')

                try:
                    working_capital_requirement = _check_is_nan(((ctx.divide(1, inventory_turnover) + ctx.divide(1, accounts_receivables_turnover) - ctx.divide(1, accounts_payable_turnover)) \
                                                 * Decimal('365')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    working_capital_requirement = Decimal('0')

                try:
                    working_capital_once = _check_is_nan(ctx.divide((revenue-operating_profit-depreciation), (working_capital_requirement/365)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    working_capital_once = Decimal('0')

                """
                성장성

                매출액성장률, 영업이익성장률, 순이익성장률, 자기자본 증가율, 총자산증가율
                """
                if before_revenue == 0:
                    revenue_growth = Decimal('0')
                else:
                    try:
                        revenue_growth = _check_is_nan(ctx.multiply(ctx.divide(revenue-before_revenue, before_revenue), Decimal('100')).\
                            quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ZeroDivisionError):
                        revenue_growth = Decimal('0')

                if before_operating_profit == 0:
                    operating_profit_growth = Decimal('0')
                else:
                    try:
                        operating_profit_growth = _check_is_nan(ctx.multiply(ctx.divide(operating_profit-before_operating_profit, before_operating_profit), Decimal('100')).\
                            quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ZeroDivisionError):
                        operating_profit_growth = Decimal('0')
                
                if before_net_profit == 0:
                    net_profit_growth = Decimal('0')
                else:
                    try:
                        net_profit_growth = _check_is_nan(ctx.multiply(ctx.divide(net_profit-before_net_profit, before_net_profit), Decimal('100')).\
                            quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ZeroDivisionError):
                        net_profit_growth = Decimal('0')

                if before_total_capital == 0:
                    net_worth_growth = Decimal('0')
                else:
                    try:
                        net_worth_growth = _check_is_nan(ctx.multiply(ctx.divide(total_capital-before_total_capital, before_total_capital), Decimal('100')).\
                            quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ZeroDivisionError):
                        net_worth_growth = Decimal('0')

                if before_total_assets == 0:
                    assets_growth = Decimal('0')
                else:
                    try:
                        assets_growth = _check_is_nan(ctx.multiply(ctx.divide(total_assets-before_total_assets, before_total_assets), Decimal('100')).\
                            quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                    except (InvalidOperation, ZeroDivisionError):
                        assets_growth = Decimal('0')

                """
                투자지표
                
                per, pbr, psr, eps, bps, ev_ebitda, ev_ocf
                """
                try:
                    per = _check_is_nan(ctx.divide(market_capitalization, net_profit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    per = Decimal('0')

                try:
                    pbr = _check_is_nan(ctx.divide(per, roe).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    pbr = Decimal('0')

                try:
                    psr = _check_is_nan(ctx.divide(market_capitalization, revenue).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    psr = Decimal('0')

                try:
                    eps = _check_is_nan(ctx.divide(ctx.multiply(net_profit, set_unit), shares_outstanding).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    eps = Decimal('0')

                try:
                    bps = _check_is_nan(ctx.divide(ctx.multiply(total_capital, set_unit), shares_outstanding).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    bps = Decimal('0')

                try:
                    ev_ebitda = _check_is_nan(ctx.divide((market_capitalization - cash_equivalents), (operating_profit + interest_expense + corporate_tax + depreciation)).\
                                              quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    ev_ebitda = Decimal('0')

                try:
                    ev_ocf = _check_is_nan(ctx.divide((market_capitalization - cash_equivalents), operating_cash_flow).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))
                except (InvalidOperation, ZeroDivisionError):
                    ev_ocf = Decimal('0')
                
                if InvestmentIndex.objects.filter(corp_id__stock_code=stock_code, year=year, quarter=quarter, fs_type=fs_type).exists():
                    index_list.append(
                        InvestmentIndex(
                            id=InvestmentIndex.objects.get(corp_id__stock_code=stock_code, year=year, quarter=quarter, fs_type=fs_type).id,
                            corp_id=CorpId.objects.get(stock_code=stock_code),
                            year=year,
                            quarter=quarter,
                            fs_type=fs_type,
                            settlement_date=document['결산기준일'],
                            revenue=revenue,
                            operating_profit=operating_profit,
                            net_profit=net_profit,
                            total_assets=total_assets,
                            total_debt=total_debt,
                            total_capital=total_capital,
                            operating_cash_flow=operating_cash_flow,
                            investing_cash_flow=investing_cash_flow,
                            financing_cash_flow=financing_cash_flow,
                            current_ratio=current_ratio,
                            quick_ratio=quick_ratio,
                            debt_ratio=debt_ratio,
                            interest_coverage_ratio=interest_coverage_ratio,
                            cost_of_sales_ratio=cost_of_sales_ratio,
                            gross_profit_margin=gross_profit_margin,
                            operating_margin=operating_margin,
                            net_profit_margin=net_profit_margin,
                            roic=roic,
                            roe=roe,
                            roa=roa,
                            total_assets_turnover=total_assets_turnover,
                            inventory_turnover=inventory_turnover,
                            accounts_receivables_turnover=accounts_receivables_turnover,
                            accounts_payable_turnover=accounts_payable_turnover,
                            working_capital_requirement=working_capital_requirement,
                            working_capital_once=working_capital_once,
                            revenue_growth=revenue_growth,
                            operating_profit_growth=operating_profit_growth,
                            net_profit_growth=net_profit_growth,
                            net_worth_growth=net_worth_growth,
                            assets_growth=assets_growth,
                            dps=dps,
                            dividend=ctx.divide(total_dividend, Decimal('100_000_000')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP),
                            dividend_ratio=dividend_ratio,
                            dividend_payout_ratio=dividend_payout_ratio,
                            per=per,
                            pbr=pbr,
                            psr=psr,
                            eps=eps,
                            bps=bps,
                            ev_ebitda=ev_ebitda,
                            ev_ocf=ev_ocf
                        )
                    )
                else:
                    index_list.append(
                        InvestmentIndex(
                            corp_id=CorpId.objects.get(stock_code=stock_code),
                            year=year,
                            quarter=quarter,
                            fs_type=fs_type,
                            settlement_date=document['결산기준일'],
                            revenue=revenue,
                            operating_profit=operating_profit,
                            net_profit=net_profit,
                            total_assets=total_assets,
                            total_debt=total_debt,
                            total_capital=total_capital,
                            operating_cash_flow=operating_cash_flow,
                            investing_cash_flow=investing_cash_flow,
                            financing_cash_flow=financing_cash_flow,
                            current_ratio=current_ratio,
                            quick_ratio=quick_ratio,
                            debt_ratio=debt_ratio,
                            interest_coverage_ratio=interest_coverage_ratio,
                            cost_of_sales_ratio=cost_of_sales_ratio,
                            gross_profit_margin=gross_profit_margin,
                            operating_margin=operating_margin,
                            net_profit_margin=net_profit_margin,
                            roic=roic,
                            roe=roe,
                            roa=roa,
                            total_assets_turnover=total_assets_turnover,
                            inventory_turnover=inventory_turnover,
                            accounts_receivables_turnover=accounts_receivables_turnover,
                            accounts_payable_turnover=accounts_payable_turnover,
                            working_capital_requirement=working_capital_requirement,
                            working_capital_once=working_capital_once,
                            revenue_growth=revenue_growth,
                            operating_profit_growth=operating_profit_growth,
                            net_profit_growth=net_profit_growth,
                            net_worth_growth=net_worth_growth,
                            assets_growth=assets_growth,
                            dps=dps,
                            dividend=ctx.divide(total_dividend, Decimal('100_000_000')).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP),
                            dividend_ratio=dividend_ratio,
                            dividend_payout_ratio=dividend_payout_ratio,
                            per=per,
                            pbr=pbr,
                            psr=psr,
                            eps=eps,
                            bps=bps,
                            ev_ebitda=ev_ebitda,
                            ev_ocf=ev_ocf
                        )
                    )

    return index_list

def _check_is_nan(value):

    if not isinstance(value, Decimal):
        value = Decimal('0')
    elif value.is_nan():
        value = Decimal('0')
    elif value is None:
        value = Decimal('0')

    return value
    
def save_investment_index(year, quarter, fs_type):
    """
    투자지표 저장
    """
    stock_codes = CorpId.objects.values_list('stock_code', flat=True)
    _download_corp_code()
    _unzip_corp_code()
    corp_list = _get_collect_corp_list(stock_codes, year, quarter)
    data = _parse_investment_index(year, quarter, fs_type, corp_list)

    # 사용한 corpCode 파일 제거
    remove_files(os.path.join(DOWNLOAD_PATH, 'corpCode.zip'))
    remove_files(os.path.join(DOWNLOAD_PATH, 'CORPCODE.xml'))

    if data:
        return data

    return False