"""
@created at 2023.05.10
@author JSU in Aimdat Team

@modified at 2023.05.23
@author JSU in Aimdat Team
"""
import os
import zipfile
import pymongo
import re
import requests
import retry
import shutil
import xml.etree.ElementTree as ET

from config.settings.base import get_secret
from decimal import (
    Context,
    Decimal,
    InvalidOperation
)
from django.db.models import Q
from services.models.corp_id import CorpId
from services.models.investment_index import InvestmentIndex
from services.models.stock_price import StockPrice

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

    with open(downlaod_path+'\\corpCode.zip', 'wb') as file:
        file.write(response.content)

def _unzip_corp_code():
    """
    Opendart의 고유번호 파일 압축해제
    """
    download_path = get_secret('download_folder')

    with zipfile.ZipFile(download_path+'\\corpCode.zip', 'r') as zip_file:
        zip_file.extract('CORPCODE.xml', download_path)

@retry.retry(exceptions=[TimeoutError, requests.exceptions.ConnectionError], tries=10, delay=3)
def _parse_investment_index(year, quarter, fs_type, stock_codes):
    """
    기업 데이터 파싱 후 투자지표 데이터로 변환
    """
    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements']

    # 정규식 패턴
    not_digit_pattern = re.compile(r'(\D|-)')
    revenue_pattern = re.compile(r'(\.?\s*(매출액|영업수익)(\(손실\)|<주석40>|:)?|^((영업|금융)?수익(\(매출액\)?)|매출액(\((영업수익|매출액)\))?)$)')
    cost_of_sales_pattern = re.compile(r'\s*.{0,3}\.?\s*영업비용|매출원가\s*(\(.{0,4}\))?$')
    operating_profit_pattern = re.compile(r'\s*.{0,3}\.?\s*총?영업이익\s*(\(.{0,4}\)|\s*)?$')
    net_profit_pattern = re.compile(r'\s*.{0,3}\.?\s*(연결)?(당기|분기)순이익\s*(\(.{0,4}\)|\s*)?$')
    inventories_pattern = re.compile(r'\s*.{0,3}\.?\s*재고자산\s*(\(.{0,4}\)|\s*)?$')
    total_debt_pattern = re.compile(r'\s*부\s*채\s*총\s*계')
    total_asset_pattern = re.compile(r'\s*자\s*산\s*총\s*계')
    total_capital_pattern = re.compile(r'\s*자\s*본\s*총\s*계')
    current_asset_pattern = re.compile(r'\s*((I|I |\u2160)\.)?\s*(유\s*동\s*자\s*산).*')
    current_liability_pattern = re.compile(r'\s*((I|I |\u2160)\.)?\s*(유\s*동\s*부\s*채).*')
    cash_and_cash_equivalents_pattern = re.compile(r'\s*.{0,4}?\s*((\(?(당|반|분)\)?)*기\s*말(의)?\s*현\s*금\s*및\s*현\s*금\s*성\s*자\s*산).*')
    interest_expense_pattern = re.compile(r'.{0,4}(이\s*자\s*비\s*용).*')
    corporate_tax_pattern = re.compile(r'\s*.{0,4}?\s*(?!법인세비용차)((계속영업)?법\s*인\s*세\s*비\s*용).*')
    depreciation_cost_pattern = re.compile(r'.*감가상각.*')
    cash_flows_from_operating_pattern = re.compile(r'영업활동\s?으?로?인?한?\s?현금흐름')
    cash_flows_from_investing_activities_pattern = re.compile(r'투자활동\s?으?로?인?한?\s?현금흐름')

    # 변수 초기화
    total_dividend = Decimal(0)
    interest_expense = Decimal(0)
    depreciation_cost = Decimal(0)

    # 재무제표 타입 {연결: 0, 별도: 5}
    if fs_type == '0':
        fs_type_regex = r'연결*'
    elif fs_type == '5':
        fs_type_regex = r'별도*'

    # 데이터 수집
    index_dict_list = []
    for stock_code in stock_codes:
        index_dict = {}
        query = {'종목코드': stock_code, '년도': int(year), '분기': int(quarter), '재무제표종류': {'$regex': fs_type_regex}}

        # 검색 결과가 없으면 넘어가기
        if collection.count_documents(query) == 0:
            continue

        # MongoDB에서 재무제표 데이터 조회        
        documents = collection.find(query)
                
        # StockPrice 값 연결
        if StockPrice.objects.filter(Q(corp_id__stock_code__exact = stock_code) & Q(trade_date__year__exact = year) & Q(trade_date__month__exact = quarter * 3)).exists():
            stock_price_obj = StockPrice.objects.filter(Q(corp_id__stock_code__exact = stock_code) & Q(trade_date__year__exact = year) & Q(trade_date__month__exact = quarter * 3)).latest('trade_date')
            market_capitalization = stock_price_obj.market_capitalization # 시가총액
            shares_outstanding = stock_price_obj.total_stock # 발행주식수
            stock_price = stock_price_obj.close_price # 주가
        else:
            market_capitalization = 0
            shares_outstanding = 0
            stock_price = 0
        
        for document in documents:

            # 계정과목 값 추출
            for key in list(document.keys()):

                if revenue_pattern.match(key):
                    try:
                        revenue = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        revenue = Decimal(0)

                    if revenue:
                        revenue = Decimal(revenue)
                    else:
                        revenue = Decimal(0)
                
                elif cost_of_sales_pattern.match(key):
                    try:
                        cost_of_sales = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        cost_of_sales = Decimal(0)

                    if cost_of_sales:
                        cost_of_sales = Decimal(cost_of_sales)
                    else:
                        cost_of_sales = Decimal(0)

                elif operating_profit_pattern.match(key):
                    try:
                        operating_profit = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        operating_profit = Decimal(0)

                    if operating_profit:
                        operating_profit = Decimal(operating_profit)
                    else:
                        operating_profit = Decimal(0)

                elif net_profit_pattern.match(key):
                    try:
                        net_profit = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        net_profit = Decimal(0)

                    if net_profit:
                        net_profit = Decimal(net_profit)
                    else:
                        net_profit = Decimal(0)

                elif inventories_pattern.match(key):
                    try:
                        inventories = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        inventories = Decimal(0)

                    if inventories:
                        inventories = Decimal(inventories)
                    else:
                        inventories = Decimal(0)
                
                elif total_debt_pattern.match(key):
                    try:
                        total_debt = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        total_debt = Decimal(0)

                    if total_debt:
                        total_debt = Decimal(total_debt)
                    else:
                        total_debt = Decimal(0)

                elif total_asset_pattern.match(key):
                    try:
                        total_asset = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        total_asset = Decimal(0)

                    if total_asset:
                        total_asset = Decimal(total_asset)
                    else:
                        total_asset = Decimal(0)

                elif total_capital_pattern.match(key):
                    try:
                        total_capital = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        total_capital = Decimal(0)

                    if total_capital:
                        total_capital = Decimal(total_capital)
                    else:
                        total_capital = Decimal(0)

                elif current_asset_pattern.match(key):
                    try:
                        current_asset = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        current_asset = Decimal(0)

                    if current_asset:
                        current_asset = Decimal(current_asset)
                    else:
                        current_asset = Decimal(0)
                
                elif current_liability_pattern.match(key):
                    try:
                        current_liability = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        current_liability = Decimal(0)

                    if current_liability:
                        current_liability = Decimal(current_liability)
                    else:
                        current_liability = Decimal(0)

                elif cash_and_cash_equivalents_pattern.match(key):
                    try:
                        cash_and_cash_equivalents = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        cash_and_cash_equivalents = Decimal(0)

                    if cash_and_cash_equivalents:
                        cash_and_cash_equivalents = Decimal(cash_and_cash_equivalents)
                    else:
                        cash_and_cash_equivalents = Decimal(0)

                elif interest_expense_pattern.match(key):
                    try:
                        interest_expense = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        interest_expense = Decimal(0)

                    if interest_expense:
                        interest_expense = Decimal(interest_expense)
                    else:
                        interest_expense = Decimal(0)

                elif corporate_tax_pattern.match(key):
                    try:
                        corporate_tax = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        corporate_tax = Decimal(0)

                    if corporate_tax:
                        corporate_tax = Decimal(corporate_tax)
                    else:
                        corporate_tax = Decimal(0)

                elif depreciation_cost_pattern.match(key):
                    try:
                        depreciation_cost = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        depreciation_cost = Decimal(0)

                    if depreciation_cost:
                        depreciation_cost = Decimal(depreciation_cost)
                    else:
                        depreciation_cost = Decimal(0)

                elif cash_flows_from_operating_pattern.match(key):
                    try:
                        cash_flows_from_operating = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        cash_flows_from_operating = Decimal(0)

                    if cash_flows_from_operating:
                        cash_flows_from_operating = Decimal(cash_flows_from_operating)
                    else:
                        cash_flows_from_operating = Decimal(0)

                elif cash_flows_from_investing_activities_pattern.match(key):
                    try:
                        cash_flows_from_investing_activities = not_digit_pattern.sub('', str(document[key].to_decimal()))
                    except AttributeError:
                        cash_flows_from_investing_activities = Decimal(0)

                    if cash_flows_from_investing_activities:
                        cash_flows_from_investing_activities = Decimal(cash_flows_from_investing_activities)
                    else:
                        cash_flows_from_investing_activities = Decimal(0)
                else:
                    continue
        
        # Opendart에서 배당데이터 수집
        url = 'https://opendart.fss.or.kr/api/alotMatter.xml'

        # XML 파일 트리 생성
        download_path = get_secret('download_folder')
        corp_code_tree = ET.parse(download_path+'\\CORPCODE.xml')
        corp_code_root = corp_code_tree.getroot()

        # corp_code 확인
        for element in corp_code_root.iter('list'):
            stock_code_element = element.find('stock_code').text

            if str(stock_code_element) == str(stock_code):
                corp_code = element.find('corp_code').text
        
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

                # API 호출
                response = requests.get(url, params=params)

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
                                    index_dict['dividend'] = Decimal(value) # 배당금 저장

                        # 현금배당금 총액 파싱
                        if re.match(r'현금배당금총액', element.find('se').text):
                            value = not_digit_pattern.sub('', element.find('thstrm').text)
                            if value:
                                total_dividend = Decimal(value) * Decimal(1000000)
                    
                    if 'dividend' not in index_dict:
                        index_dict['dividend'] = Decimal(0)
                
                # 나눗셈 정확도 설정
                ctx = Context(prec=6)

                # 이익관련
                try:
                    index_dict['cost_of_sales_ratio'] = ctx.divide(cost_of_sales, revenue) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['cost_of_sales_ratio'] = Decimal(0)

                try:
                    index_dict['operating_margin'] = ctx.divide(operating_profit, revenue) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['operating_margin'] = Decimal(0)

                try:
                    index_dict['net_profit_margin'] = ctx.divide(net_profit, revenue) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['net_profit_margin'] = Decimal(0)

                try:
                    index_dict['roe'] = ctx.divide(net_profit, total_capital) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['roe'] = Decimal(0)

                try:
                    index_dict['roa'] = ctx.divide(net_profit, total_asset) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['roa'] = Decimal(0)

                # 현금관련
                try:
                    index_dict['current_ratio'] = ctx.divide(current_asset, current_liability) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['current_ratio'] = Decimal(0)

                try:
                    index_dict['quick_ratio'] = ctx.divide((current_asset - inventories), current_liability) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['quick_ratio'] = Decimal(0)

                try:
                    index_dict['debt_ratio'] = ctx.divide(total_debt, total_capital) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['debt_ratio'] = Decimal(0)

                # 주가관련
                try:
                    index_dict['per'] = ctx.divide(market_capitalization, net_profit)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['per'] = Decimal(0)

                try:
                    index_dict['pbr'] = ctx.divide(index_dict['per'], index_dict['roe'])
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['pbr'] = Decimal(0)

                try:
                    index_dict['psr'] = ctx.divide(market_capitalization, revenue)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['psr'] = Decimal(0)

                try:
                    index_dict['eps'] = ctx.divide(net_profit, shares_outstanding)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['eps'] = Decimal(0)

                try:
                    index_dict['bps'] = ctx.divide(total_capital, shares_outstanding)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['bps'] = Decimal(0)

                try:
                    index_dict['dps'] = ctx.divide(total_dividend, shares_outstanding)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['dps'] = Decimal(0)

                # 현금흐름관련
                try:
                    index_dict['ev_ebitda'] = ctx.divide((market_capitalization - cash_and_cash_equivalents), (operating_profit + interest_expense + corporate_tax + depreciation_cost))
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['ev_ebitda'] = Decimal(0)

                try:
                    index_dict['ev_ocf'] = ctx.divide((market_capitalization - cash_and_cash_equivalents), cash_flows_from_operating)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['ev_ocf'] = Decimal(0)

                # 배당관련
                try:
                    index_dict['dividend_ratio'] = ctx.divide(index_dict['dps'], stock_price) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['dividend_ratio'] = Decimal(0)

                try:
                    index_dict['payout_ratio'] = ctx.divide(index_dict['dps'], index_dict['eps']) * Decimal(100)
                except (InvalidOperation, ZeroDivisionError):
                    index_dict['payout_ratio'] = Decimal(0)

                # 수치데이터
                index_dict['stock_code'] = stock_code # 종목코드
                index_dict['revenue'] = revenue
                index_dict['operating_profit'] = operating_profit
                index_dict['net_profit'] = net_profit

                index_dict_list.append(index_dict)
                continue
    
    return index_dict_list

def _remove_file(file_path, folder=False):
    """
    사용한 파일 제거
    """
    if folder:
        try:
            shutil.rmtree(file_path)
        except OSError:
            pass
    else:
        try:
            os.remove(file_path)
        except OSError:
            pass
    
def save_investment_index(year, quarter, fs_type):
    """
    투자지표 저장
    """
    stock_codes = CorpId.objects.values_list('stock_code', flat=True)

    _download_corp_code()
    _unzip_corp_code()
    data = _parse_investment_index(year, quarter, fs_type, stock_codes)

    for d in data:
        InvestmentIndex.objects.create(
            corp_id=CorpId.objects.get(stock_code=d['stock_code']),
            year=year, 
            quarter=quarter,
            fs_type=fs_type, 
            revenue=d['revenue'], 
            operating_profit=d['operating_profit'],
            net_profit=d['net_profit'],                                                                 
            cost_of_sales_ratio=d['cost_of_sales_ratio'], 
            operating_margin=d['operating_margin'],
            net_profit_margin=d['net_profit_margin'], 
            roe=d['roe'],
            roa=d['roa'], 
            current_ratio=d['current_ratio'], 
            quick_ratio=d['quick_ratio'],
            debt_ratio=d['debt_ratio'], 
            per=d['per'], 
            pbr=d['pbr'],
            psr=d['psr'], 
            eps=d['eps'], 
            bps=d['bps'], 
            dps=d['dps'], 
            ev_ebitda=d['ev_ebitda'],
            ev_ocf=d['ev_ocf'], 
            dividend=d['dividend'],
            dividend_ratio=d['dividend_ratio'], 
            dividend_payout_ratio=d['payout_ratio']
        )
        
    # 사용한 corpCode 파일 제거
    _remove_file(os.path.join(get_secret('download_folder'), 'corpCode.zip'))
    _remove_file(os.path.join(get_secret('download_folder'), 'CORPCODE.xml'))
