"""
@created at 2023.05.10
@author JSU in Aimdat Team

@modified at 2023.06.19
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
from config.settings.base import get_secret
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

DOWNLOAD_PATH = get_secret('download_folder')

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

def _parse_investment_index(year, quarter, fs_type, stock_codes):
    """
    기업 데이터 파싱 후 투자지표 데이터로 변환
    """
    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements6']

    # 정규식 패턴
    not_digit_pattern = re.compile(r'\D')
    revenue_pattern = re.compile(r'(\s*.{0,3}\.?\s*(매출액|영업수익)(\(손실\)|<주석40>|:)?|^((영업|금융)?수익(\(매출액\)?)|매출액?(\((영업수익|매출액)\))?)$)')
    cost_of_sales_pattern = re.compile(r'\s*.{0,3}\.?\s*(영업비용|매출원가)\s*(\(.{0,4}\))?$')
    operating_profit_pattern = re.compile(r'^\s*(?!.*(기타|세후|계속|정상|매출|중단|주당)).{0,3}\.?\s*?총?((영업|포괄)(이익|손익|수익|매출총이익|당\s*기\s*순\s*이\s*익))\s*(\(.{0,4}\)|\s*)?$')
    net_profit_pattern = re.compile(r'\s*.{0,3}\.?\s*(연결)?(당기|분기|반기)총?(의\s*)?(포괄)?순?(이익|손익|손실)\s*(\(.{0,4}\)|\s*)?$')
    inventories_pattern = re.compile(r'\s*.{0,3}\.?\s*재고자산\s*(\(.{0,4}\))?$')
    total_debt_pattern = re.compile(r'\s*부\s*채\s*총\s*계')
    total_asset_pattern = re.compile(r'\s*자\s*산\s*총\s*계')
    total_capital_pattern = re.compile(r'\s*자\s*본\s*총\s*계')
    current_asset_pattern = re.compile(r'^(?!\s*(비|기타))\s*.{0,3}\.?\s*((?!기타)유\s*동\s*자\s*산).*')
    current_liability_pattern = re.compile(r'^(?!\s*(비|기타))\s*.{0,3}\.?\s*((?!기타)유\s*동\s*부\s*채).*')
    cash_and_cash_equivalents_pattern = re.compile(r'\s*.{0,4}?\s*((\(?(당|반|분)\)?)*기\s*말(의)?\s*현\s*금\s*및\s*현\s*금\s*성\s*자\s*산).*')
    interest_expense_pattern = re.compile(r'.{0,4}(이\s*자\s*비\s*용).*')
    corporate_tax_pattern = re.compile(r'\s*.{0,4}?\s*(?!법인세비용차)((계속영업)?법\s*인\s*세\s*비\s*용).*')
    depreciation_cost_pattern = re.compile(r'.*감가상각.*')
    cash_flows_from_operating_pattern = re.compile(r'영업활동\s?으?로?인?한?\s?현금흐름')

    # 재무제표 타입 {연결: 0, 별도: 5}
    if fs_type == '0':
        fs_type_regex = '연결'
    elif fs_type == '5':
        fs_type_regex = '별도'

    # 데이터 수집
    index_dict_list = []
    for stock_code in stock_codes:
        index_dict = {}
        index_dict['year'] = year
        index_dict['quarter'] = quarter
        index_dict['fs_type'] = fs_type
        query = {'종목코드': stock_code, '년도': year, '분기': quarter, '재무제표종류': {'$regex': fs_type_regex}}

        # 검색 결과가 없으면 넘어가기
        if collection.count_documents(query) == 0:
            continue
        
        # MongoDB에서 재무제표 데이터 조회        
        documents = collection.find(query)

        """
        계정 과목 설정
        매출액, 매출원가, 영업이익, 당기순이익의 경우 가장 처음 매칭된 값만 저장하도록 설정함.
        """
        matched_revenue = True
        matched_cost_of_sales = True
        matched_operating_profit = True
        matched_net_profit = True

        # 변수 초기화
        revenue = Decimal('0')
        cost_of_sales = Decimal('0')
        operating_profit = Decimal('0')
        net_profit = Decimal('0')
        inventories = Decimal('0')
        total_debt = Decimal('0')
        total_asset = Decimal('0')
        total_capital = Decimal('0')
        current_asset = Decimal('0')
        current_liability = Decimal('0')
        cash_and_cash_equivalents = Decimal('0')
        interest_expense = Decimal('0')
        corporate_tax = Decimal('0')
        depreciation_cost = Decimal('0')
        cash_flows_from_operating = Decimal('0')
        total_dividend = Decimal('0')
        interest_expense = Decimal('0')
        depreciation_cost = Decimal('0')

        # 나눗셈 정확도 설정
        ctx = Context(prec=6)

        # 단위 설정
        set_unit = Decimal('100_000_000')
                
        # StockPrice 값 연결
        if StockPrice.objects.annotate(date_field=Cast(F('trade_date'), output_field=DateField())).filter(Q(corp_id__stock_code__exact = stock_code) & Q(date_field__year__exact = year) & Q(date_field__month__exact = quarter * 3)).exists():
            stock_price_obj = StockPrice.objects.annotate(date_field=Cast(F('trade_date'), output_field=DateField())).filter(Q(corp_id__stock_code__exact = stock_code) & Q(date_field__year__exact = year) & Q(date_field__month__exact = quarter * 3)).latest('date_field')
            market_capitalization = ctx.divide(stock_price_obj.market_capitalization, set_unit) # 시가총액
            shares_outstanding = stock_price_obj.total_stock # 발행주식수
            stock_price = stock_price_obj.close_price # 주가
        else:
            # A603 로깅
            LOGGER.info('[A603] 저장된 주가 정보가 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
            market_capitalization = 0
            shares_outstanding = 0
            stock_price = 0
        
        for document in documents:
            # 단위 설정
            if document['단위'] == '천원':
                set_unit = Decimal('100_000')
            elif document['단위'] == '백만원':
                set_unit = Decimal('100')

            # 계정과목 값 추출
            for key in list(document.keys()):

                if revenue_pattern.match(key) and matched_revenue:
                    try:
                        revenue = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        matched_revenue = False
                    except:
                        revenue = Decimal('0')
                
                elif cost_of_sales_pattern.match(key) and matched_cost_of_sales:
                    try:
                        cost_of_sales = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        matched_cost_of_sales = False
                    except:
                        cost_of_sales = Decimal('0')

                elif operating_profit_pattern.match(key) and matched_operating_profit:
                    try:
                        operating_profit = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        matched_operating_profit = False
                    except:
                        operating_profit = Decimal('0')

                elif net_profit_pattern.match(key) and matched_net_profit:
                    try:
                        net_profit = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        matched_net_profit = False
                    except:
                        net_profit = Decimal('0')

                elif inventories_pattern.match(key):
                    try:
                        inventories = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        inventories = Decimal('0')
                
                elif total_debt_pattern.match(key):
                    try:
                        total_debt = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        total_debt = Decimal('0')

                elif total_asset_pattern.match(key):
                    try:
                        total_asset = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        total_asset = Decimal('0')

                elif total_capital_pattern.match(key):
                    try:
                        total_capital = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        total_capital = Decimal('0')

                elif current_asset_pattern.match(key):
                    try:
                        current_asset = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        current_asset = Decimal('0')
                
                elif current_liability_pattern.match(key):
                    try:
                        current_liability = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        current_liability = Decimal('0')

                elif cash_and_cash_equivalents_pattern.match(key):
                    try:
                        cash_and_cash_equivalents = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        cash_and_cash_equivalents = Decimal('0')

                elif interest_expense_pattern.match(key):
                    try:
                        interest_expense = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        interest_expense = Decimal('0')

                elif corporate_tax_pattern.match(key):
                    try:
                        corporate_tax = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        corporate_tax = Decimal('0')

                elif depreciation_cost_pattern.match(key):
                    try:
                        depreciation_cost = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        depreciation_cost = Decimal('0')

                elif cash_flows_from_operating_pattern.match(key):
                    try:
                        cash_flows_from_operating = ctx.divide(Decimal(str(document[key].to_decimal())), set_unit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    except:
                        cash_flows_from_operating = Decimal('0')
                else:
                    continue
        
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
                        # 주당 현금배당금(보통주) 파싱(단위: 원)
                        if element.find('stock_knd') != None:
                            stock_knd = element.find('stock_knd').text
                            se = element.find('se').text

                            if stock_knd == '보통주' and se == '주당 현금배당금(원)':
                                value = not_digit_pattern.sub('', element.find('thstrm').text)
                                if value:
                                    index_dict['dividend'] = Decimal(value).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP) # 배당금 저장

                        # 현금배당금 총액 파싱
                        if re.match(r'현금배당금총액', element.find('se').text):
                            value = not_digit_pattern.sub('', element.find('thstrm').text)
                            if value:
                                total_dividend_value = Decimal(value) * Decimal('1_000_000')
                                total_dividend = total_dividend_value.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    
                    if 'dividend' not in index_dict:
                        # A604 로깅
                        LOGGER.info('[A604] 배당정보 없음. {}, {}, {}, {}'.format(str(stock_code), str(year), str(quarter), str(fs_type)))
                        index_dict['dividend'] = Decimal('0')
                
                # 이익관련
                try:
                    cost_of_sales_ratio = ctx.divide(cost_of_sales, revenue) * Decimal('100')
                    index_dict['cost_of_sales_ratio'] = cost_of_sales_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['cost_of_sales_ratio'] = Decimal('0')

                try:
                    operating_margin = ctx.divide(operating_profit, revenue) * Decimal('100')
                    index_dict['operating_margin'] = operating_margin.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['operating_margin'] = Decimal('0')

                try:
                    net_profit_margin = ctx.divide(net_profit, revenue) * Decimal('100')
                    index_dict['net_profit_margin'] = net_profit_margin.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['net_profit_margin'] = Decimal('0')

                try:
                    roe = ctx.divide(net_profit, total_capital) * Decimal('100')
                    index_dict['roe'] = roe.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['roe'] = Decimal('0')

                try:
                    roa = ctx.divide(net_profit, total_asset) * Decimal('100')
                    index_dict['roa'] = roa.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['roa'] = Decimal('0')

                # 현금관련
                try:
                    current_ratio = ctx.divide(current_asset, current_liability) * Decimal('100')
                    index_dict['current_ratio'] = current_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['current_ratio'] = Decimal('0')

                try:
                    quick_ratio = ctx.divide((current_asset - inventories), current_liability) * Decimal('100')
                    index_dict['quick_ratio'] = quick_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['quick_ratio'] = Decimal('0')

                try:
                    debt_ratio = ctx.divide(total_debt, total_capital) * Decimal('100')
                    index_dict['debt_ratio'] = debt_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['debt_ratio'] = Decimal('0')

                # 주가관련
                try:
                    index_dict['per'] = ctx.divide(market_capitalization, net_profit).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['per'] = Decimal('0')

                try:
                    index_dict['pbr'] = ctx.divide(index_dict['per'], index_dict['roe']).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['pbr'] = Decimal('0')

                try:
                    index_dict['psr'] = ctx.divide(market_capitalization, revenue).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['psr'] = Decimal('0')

                try:
                    index_dict['eps'] = ctx.divide(ctx.multiply(net_profit, set_unit), shares_outstanding).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['eps'] = Decimal('0')

                try:
                    index_dict['bps'] = ctx.divide(ctx.multiply(total_capital, set_unit), shares_outstanding).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['bps'] = Decimal('0')

                try:
                    index_dict['dps'] = ctx.divide(total_dividend, shares_outstanding).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['dps'] = Decimal('0')

                # 현금흐름관련
                try:
                    index_dict['ev_ebitda'] = ctx.divide((market_capitalization - cash_and_cash_equivalents), (operating_profit + interest_expense + corporate_tax + depreciation_cost)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['ev_ebitda'] = Decimal('0')

                try:
                    index_dict['ev_ocf'] = ctx.divide((market_capitalization - cash_and_cash_equivalents), cash_flows_from_operating).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['ev_ocf'] = Decimal('0')

                # 배당관련
                try:
                    dividend_ratio = ctx.divide(index_dict['dps'], stock_price) * Decimal('100')
                    index_dict['dividend_ratio'] = dividend_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['dividend_ratio'] = Decimal('0')

                try:
                    payout_ratio = ctx.divide(index_dict['dps'], index_dict['eps']) * Decimal('100')
                    index_dict['payout_ratio'] = payout_ratio.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['payout_ratio'] = Decimal('0')

                # 종목코드
                index_dict['stock_code'] = stock_code
                # 수치데이터
                index_dict['revenue'] = revenue
                index_dict['operating_profit'] = operating_profit
                index_dict['net_profit'] = net_profit

                # NaN 데이터 처리
                for key, value in index_dict.items():
                    if not isinstance(value, Decimal):
                        continue
                    if value.is_nan():
                        index_dict[key] = Decimal('0')

                index_dict_list.append(index_dict)
    
    return index_dict_list
    
def save_investment_index(year, quarter, fs_type):
    """
    투자지표 저장
    """
    stock_codes = CorpId.objects.values_list('stock_code', flat=True)

    _download_corp_code()
    _unzip_corp_code()
    data = _parse_investment_index(year, quarter, fs_type, stock_codes)

    # 사용한 corpCode 파일 제거
    remove_files(os.path.join(DOWNLOAD_PATH, 'corpCode.zip'))
    remove_files(os.path.join(DOWNLOAD_PATH, 'CORPCODE.xml'))

    if data:
        return data

    return False
