"""
@created at 2023.05.10
@author JSU in Aimdat Team
"""

import re
import xml.etree.ElementTree as ET
from decimal import Decimal

import pymongo
import requests
from django.db.models import Q

from config.settings.base import get_secret
from services.models.corp_id import CorpId
from services.models.investment_index import InvestmentIndex
from services.models.stock_price import StockPrice


def get_data_with_nosql():
    """
    재무정보수집(MongoDB)
    """
    # MongoDB 연결
    client = pymongo.MongoClient('localhost:27017')
    db = client['aimdat']
    collection = db['financial_statements']

    # 정규식 패턴
    not_digit_pattern = re.compile('(\D|-)')
    revenue_pattern = re.compile('\.?\s*영업수익(\(손실\)|<주석40>|:)?')
    cost_of_sales_pattern = re.compile('\s*.{0,5}\.?\s*영업비용\s*(\(.{0,4}\))?$')
    operating_profit_pattern = re.compile('\s*.{0,5}\.?\s*총?영업이익\s*(\(.{0,4}\)|\s*)?$')
    net_profit_pattern = re.compile('\s*.{0,5}\.?\s*(연결)?(당기|분기)순이익\s*(\(.{0,4}\)|\s*)?$')
    inventories_pattern = re.compile('\s*.{0,5}\.?\s*재고자산\s*(\(.{0,4}\)|\s*)?$')
    total_debt_pattern = re.compile('(?!(자본과)?\s?)부\s?채\s?총\s?계')
    total_asset_pattern = re.compile('자\s?산\s?총\s*?계')
    total_capital_pattern = re.compile('\s*(자\s*본\s*총\s*계\s)\s*')
    current_asset_pattern = re.compile('\s*((I|I |\u2160)\.)?\s*(유\s*동\s*자\s*산).*')
    current_liability_pattern = re.compile('\s*((I|I |\u2160)\.)?\s*(유\s*동\s*부\s*채).*')
    cash_and_cash_equivalents_pattern = re.compile('\s*.{0,4}?\s*((\(?(당|반|분)\)?)*기\s*말(의)?\s*현\s*금\s*및\s*현\s*금\s*성\s*자\s*산).*')
    interest_expense_pattern = re.compile('.{0,4}(이\s*자\s*비\s*용).*')
    corporate_tax_pattern = re.compile('\s*.{0,4}?\s*(?!법인세비용차)((계속영업)?법\s*인\s*세\s*비\s*용).*')
    depreciation_cost_pattern = re.compile('.*감가상각.*')
    cash_flows_from_operating_pattern = re.compile('영업활동\s?으?로?인?한?\s?현금흐름')
    cash_flows_from_investing_activities_pattern = re.compile('투자활동\s?으?로?인?한?\s?현금흐름')

    # 반복 값 설정
    corp_info = CorpId.objects.values_list('id', 'stock_code')
    years = [2022, 2021, 2020]
    quarters = [4, 3, 2, 1]

    # 데이터 수집
    for corp_id, stock_code in corp_info:
        count = collection.count_documents({'종목코드': stock_code})
        if count == 0:
            continue

        for year in years:
            count = collection.count_documents({'종목코드': stock_code, '년도': year})
            if count == 0:
                continue

            for quarter in quarters:
                count = collection.count_documents({'종목코드': stock_code, '년도': year, '분기': quarter})
                if count == 0:
                    continue
                else:
                    # 값 초기화
                    documents = collection.find({'종목코드': stock_code, '년도': year, '분기': quarter})
                    revenue = 0 # 매출액(영업수익)
                    cost_of_sales = 0 # 매출원가(영업비용)
                    operating_profit = 0 # 영업이익
                    net_profit = 0 # 당기순이익
                    inventories = 0 # 재고자산
                    total_debt = 0 # 총부채
                    total_asset = 0 # 총자산
                    total_capital = 0 # 총자본
                    current_asset = 0 # 유동자산
                    current_liability = 0 # 유동부채
                    cash_and_cash_equivalents = 0 # 현금성자산
                    interest_expense = 0 # 이자비용
                    corporate_tax = 0 # 법인세비용
                    depreciation_cost = 0 # 감가상각비
                    cash_flows_from_operating = 0 # 현금흐름(영업활동)
                    cash_flows_from_investing_activities = 0 # 현금흐름(투자활동)
                    dps = 0 # 주당배당금
                    total_dividend = 0 # 총배당금

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
                    # 매칭 값 추출
                    for key in list(document.keys()):
                        if revenue_pattern.match(key):
                            field = revenue_pattern.match(key).group()
                            try:
                                revenue = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                revenue = not_digit_pattern.sub('', document[field])
                            if revenue:
                                revenue = Decimal(revenue)
                            else:
                                revenue = 0
                            
                        elif cost_of_sales_pattern.match(key):
                            field = cost_of_sales_pattern.match(key).group()
                            try:
                                cost_of_sales = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                cost_of_sales = not_digit_pattern.sub('', document[field])
                            if cost_of_sales:
                                cost_of_sales = Decimal(cost_of_sales)
                            else:
                                cost_of_sales = 0

                        elif operating_profit_pattern.match(key):
                            field = operating_profit_pattern.match(key).group()
                            try:
                                operating_profit = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                operating_profit = not_digit_pattern.sub('', document[field])
                            if operating_profit:
                                operating_profit = Decimal(operating_profit)
                            else:
                                operating_profit = 0

                        elif net_profit_pattern.match(key):
                            field = net_profit_pattern.match(key).group()
                            try:
                                net_profit = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                net_profit = not_digit_pattern.sub('', document[field])
                            if net_profit:
                                net_profit = Decimal(net_profit)
                            else:
                                net_profit = 0

                        elif inventories_pattern.match(key):
                            field = inventories_pattern.match(key).group()
                            try:
                                inventories = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                inventories = not_digit_pattern.sub('', document[field])
                            if inventories:
                                inventories = Decimal(inventories)
                            else:
                                inventories = 0

                        elif total_debt_pattern.match(key):
                            field = total_debt_pattern.match(key).group()
                            try:
                                total_debt = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                total_debt = not_digit_pattern.sub('', document[field])
                            if total_debt:
                                total_debt = Decimal(total_debt)
                            else:
                                total_debt = 0

                        elif total_asset_pattern.match(key):
                            field = total_asset_pattern.match(key).group()
                            try:
                                total_asset = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                total_asset = not_digit_pattern.sub('', document[field])
                            if total_asset:
                                total_asset = Decimal(total_asset)
                            else:
                                total_asset = 0

                        elif total_capital_pattern.match(key):
                            field = total_capital_pattern.match(key).group()
                            try:
                                total_capital = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                total_capital = not_digit_pattern.sub('', document[field])
                            if total_capital:
                                total_capital = Decimal(total_capital)
                            else:
                                total_capital = 0

                        elif current_asset_pattern.match(key):
                            field = current_asset_pattern.match(key).group()
                            try:
                                current_asset = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                current_asset = not_digit_pattern.sub('', document[field])
                            if current_asset:
                                current_asset = Decimal(current_asset)
                            else:
                                current_asset = 0
                            
                        elif current_liability_pattern.match(key):
                            field = current_liability_pattern.match(key).group()
                            try:
                                current_liability = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                current_liability = not_digit_pattern.sub('', document[field])
                            if current_liability:
                                current_liability = Decimal(current_liability)
                            else:
                                current_liability = 0

                        elif cash_and_cash_equivalents_pattern.match(key):
                            field = cash_and_cash_equivalents_pattern.match(key).group()
                            try:
                                cash_and_cash_equivalents = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                cash_and_cash_equivalents = not_digit_pattern.sub('', document[field])
                            if cash_and_cash_equivalents:
                                cash_and_cash_equivalents = Decimal(cash_and_cash_equivalents)
                            else:
                                cash_and_cash_equivalents = 0

                        elif interest_expense_pattern.match(key):
                            field = interest_expense_pattern.match(key).group()
                            try:
                                interest_expense = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                interest_expense = not_digit_pattern.sub('', document[field])
                            if interest_expense:
                                interest_expense = Decimal(interest_expense)
                            else:
                                interest_expense = 0

                        elif corporate_tax_pattern.match(key):
                            field = corporate_tax_pattern.match(key).group()
                            try:
                                corporate_tax = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                corporate_tax = not_digit_pattern.sub('', document[field])
                            if corporate_tax:
                                corporate_tax = Decimal(corporate_tax)
                            else:
                                corporate_tax = 0

                        elif depreciation_cost_pattern.match(key):
                            field = depreciation_cost_pattern.match(key).group()
                            try:
                                depreciation_cost = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                depreciation_cost = not_digit_pattern.sub('', document[field])
                            if depreciation_cost:
                                depreciation_cost = Decimal(depreciation_cost)
                            else:
                                depreciation_cost = 0

                        elif cash_flows_from_operating_pattern.match(key):
                            field = cash_flows_from_operating_pattern.match(key).group()
                            try:
                                cash_flows_from_operating = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                cash_flows_from_operating = not_digit_pattern.sub('', document[field])
                            if cash_flows_from_operating:
                                cash_flows_from_operating = Decimal(cash_flows_from_operating)
                            else:
                                cash_flows_from_operating = 0

                        elif cash_flows_from_investing_activities_pattern.match(key):
                            field = cash_flows_from_investing_activities_pattern.match(key).group()
                            try:
                                cash_flows_from_investing_activities = not_digit_pattern.sub('', document[field])
                            except KeyError:
                                field = field + '\n'
                                cash_flows_from_investing_activities = not_digit_pattern.sub('', document[field])
                            if cash_flows_from_investing_activities:
                                cash_flows_from_investing_activities = Decimal(cash_flows_from_investing_activities)
                            else:
                                cash_flows_from_investing_activities = 0

                        else:
                            pass

                """
                배당정보 수집(OPENDART API)
                """
                url = 'https://opendart.fss.or.kr/api/alotMatter.xml'
                crtfc_key = get_secret("crtfc_key")

                # XML 파일 트리 생성
                corp_code_tree = ET.parse('admin_dashboard\modules\collect\CORPCODE.xml')
                corp_code_root = corp_code_tree.getroot()

                # corp_code 확인
                for element in corp_code_root.iter('list'):
                    stock_code_element = element.find('stock_code').text

                    if stock_code_element == stock_code:
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
                else:
                    reprt_code = 0
                # API 호출
                response = requests.get(url, params={'crtfc_key': crtfc_key, 'corp_code': corp_code, 'bsns_year': year, 'reprt_code': reprt_code})

                if response.status_code == 200:
                    # 반환데이터 트리 생성
                    xml_data = response.text
                    api_root = ET.fromstring(xml_data)

                    for element in api_root.iter('list'):
                        se_element = element.find('se').text

                        if '현금배당금총액(백만원)' in se_element:
                            value = not_digit_pattern.sub('', element.find('thstrm').text)
                            if value:
                                total_dividend = Decimal(value) * 1000000

                # 이익관련
                try:
                    cost_of_sales_ratio = round(cost_of_sales / revenue * 100, 2) # 매출원가율
                except ZeroDivisionError:
                    cost_of_sales_ratio = 0
                try:
                    operating_margin = round(operating_profit / revenue * 100, 2) # 영업이익률
                except ZeroDivisionError:
                    operating_margin = 0
                try:
                    net_profit_margin = round(net_profit / revenue * 100, 2) # 순이익률
                except ZeroDivisionError:
                    net_profit_margin = 0
                try:
                    roe = round(net_profit / total_capital * 100, 2)
                except ZeroDivisionError:
                    roe = 0
                try:
                    roa = round(net_profit / total_asset * 100, 2)
                except ZeroDivisionError:
                    roa = 0
                # 현금관련
                try:
                    current_ratio = round(current_asset / current_liability * 100, 2) # 유동비율
                except ZeroDivisionError:
                    current_ratio = 0
                try:
                    quick_ratio = round((current_asset - inventories) / current_liability * 100, 2) # 당좌비율
                except ZeroDivisionError:
                    quick_ratio = 0
                try:
                    debt_ratio = round(total_debt / total_capital * 100, 2) # 부채비율
                except ZeroDivisionError:
                    debt_ratio = 0
                # 주가관련
                try:
                    per = round(market_capitalization / net_profit, 2)
                except ZeroDivisionError:
                    per = 0
                try:
                    pbr = round(per * roe, 2)
                except ZeroDivisionError:
                    pbr = 0
                try:
                    psr = round(market_capitalization / revenue, 2)
                except ZeroDivisionError:
                    psr = 0
                try:
                    eps = round(net_profit / shares_outstanding, 2)
                except ZeroDivisionError:
                    eps = 0
                try:
                    bps = round(total_capital / shares_outstanding, 2)
                except ZeroDivisionError:
                    bps = 0
                try:
                    dps = round(total_dividend / shares_outstanding, 2)
                except ZeroDivisionError:
                    dps = 0
                # 현금흐름관련
                try:
                    ev_ebitda = round((market_capitalization - cash_and_cash_equivalents) / (operating_profit + interest_expense + corporate_tax + depreciation_cost), 2)
                except ZeroDivisionError:
                    ev_ebitda = 0
                try:
                    ev_ocf = round((market_capitalization - cash_and_cash_equivalents) / cash_flows_from_operating, 2)
                except ZeroDivisionError:
                    ev_ocf = 0
                # 배당관련
                try:
                    dividend_ratio = round(dps / stock_price * 100, 2) # 배당률
                except ZeroDivisionError:
                    dividend_ratio = 0
                try:
                    payout_ratio = round(dps / eps * 100, 2) # 배당성향
                except ZeroDivisionError:
                    payout_ratio = 0

                """
                postgresql에 값 저장
                """
                InvestmentIndex.objects.create(corp_id=CorpId.objects.get(id=corp_id), year=year, quarter=quarter, revenue=revenue, cost_of_sales=cost_of_sales, operating_profit=operating_profit,\
                                            net_profit=net_profit, inventories=inventories, total_debt=total_debt, total_asset=total_asset, total_capital=total_capital,\
                                                current_asset=current_asset, current_liability=current_liability, cash_and_cash_equivalents=cash_and_cash_equivalents,\
                                                    interest_expense=interest_expense, corporate_tax=corporate_tax, depreciation_cost=depreciation_cost,\
                                                        cash_flows_from_operating=cash_flows_from_operating, cash_flows_from_investing_activities=cash_flows_from_investing_activities,\
                                                            total_dividend=total_dividend, cost_of_sales_ratio=cost_of_sales_ratio, operating_margin=operating_margin,\
                                                                net_profit_margin=net_profit_margin, roe=roe, roa=roa, current_ratio=current_ratio, quick_ratio=quick_ratio,\
                                                                    debt_ratio=debt_ratio, per=per, pbr=pbr, psr=psr, eps=eps, bps=bps, dps=dps, ev_ebitda=ev_ebitda,\
                                                                        ev_ocf=ev_ocf, dividend_ratio=dividend_ratio, payout_ratio=payout_ratio)
