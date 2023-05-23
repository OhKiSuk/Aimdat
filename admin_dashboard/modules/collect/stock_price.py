"""
@created at 2023.04.04
@author cslee in Aimdat Team

@modified at 2023.05.17
@author OKS in Aimdat Team
"""       
import requests
import retry
import time

from datetime import datetime
from decimal import (
    Decimal,
    ROUND_DOWN
)

from admin_dashboard.models.last_collect_date import LastCollectDate
from config.settings.base import get_secret
from django.db.models import Q
from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice
from ..api_error.open_api_error import check_open_api_errors

def _check_is_new(stock_code):
    """
    주가정보를 처음 수집하는 기업 구분
    """
    corp_id = CorpId.objects.get(stock_code=stock_code).id
    if StockPrice.objects.filter(corp_id=corp_id).exists():
        return False
    else:
        return True
    
@retry.retry(exceptions=TimeoutError, tries=10, delay=3)
def _collect_stock_price(stock_codes, last_collect_date):
    """
    주가 정보가 수집된 적이 없는 신규 기업 종목의 주가 수집

    공공데이터포털 금융위원회_주식시세정보 중 주식시세 API 사용
    """
    url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo'

    fail_logs = []
    stock_price_data_list = []
    for stock_code in stock_codes:
        is_new = _check_is_new(stock_code)

        if is_new:
            beginBasDt = '20200102'
        else:
            beginBasDt = last_collect_date

        params = {
            'serviceKey':get_secret('data_portal_key'), 
            'numOfRows':100000000, 
            'pageNo':1, 
            'resultType':'json', 
            'beginBasDt':beginBasDt,
            'likeSrtnCd':stock_code
        }

        response = requests.get(url, params=params, verify=False)
        time.sleep(0.5)
        if response.status_code == 422:
            fail_logs.append(
                {
                    'error_code': '300',
                    'error_rank': 'danger',
                    'error_detail': stock_code + ', INVALID REQUEST PARAMETER ERROR.',
                    'error_time': datetime.now()
                }
            )
        elif response.status_code == 500:
            fail_logs.append(
                {
                    'error_code': '300',
                    'error_rank': 'danger',
                    'error_detail': stock_code + ', DB_ERROR.',
                    'error_time': datetime.now()
                }
            )
                
        try:
            response_to_json = response.json()
        except ValueError:
            # OpenAPI 에러처리
            open_api_err_log = check_open_api_errors(response)
            fail_logs.append(open_api_err_log)
            break

        dict_list = response_to_json['response']['body']['items']['item']

        basDt, clpr, vs, fltRt, mkp, hipr, lopr, trqu, trPrc, lstgStCnt, mrktTotAmt = \
        'basDt', 'clpr', 'vs', 'fltRt', 'mkp', 'hipr', 'lopr', 'trqu', 'trPrc', 'lstgStCnt', 'mrktTotAmt'

        if len(dict_list) < 1:
            fail_logs.append(
                {
                    'error_code': '',
                    'error_rank': 'info',
                    'error_detail': stock_code+', NO_RESULTS_FOUND_AT_STOCK_PRICE',
                    'error_time': datetime.now(),
                }
            )
            continue
        
        for x in dict_list:
            stock_price_data = {}
            trade_date = datetime.strptime(x[basDt], '%Y%m%d').strftime('%Y-%m-%d')
            tmp = [x[mkp], x[hipr], x[lopr], x[clpr], x[lstgStCnt], x[mrktTotAmt], x[trqu], x[trPrc], x[vs], x[fltRt]]

            # Decimal Type으로 변환
            tmp = [Decimal(str(x)).quantize(Decimal('0.' + '0'*6), rounding=ROUND_DOWN) for x in tmp]
            open_price, high_price, low_price, close_price, total_stock, market_capitalization, trade_quantity, trade_price, change_price, change_rate = tmp

            stock_price_data['corp_id'] = CorpId.objects.get(stock_code=stock_code)
            stock_price_data['trade_date'] = trade_date
            stock_price_data['open_price'] = open_price
            stock_price_data['high_price'] = high_price
            stock_price_data['low_price'] = low_price
            stock_price_data['close_price'] = close_price
            stock_price_data['total_stock'] = total_stock
            stock_price_data['market_capitalization'] = market_capitalization
            stock_price_data['trade_quantity'] = trade_quantity
            stock_price_data['trade_price'] = trade_price
            stock_price_data['change_price'] = change_price
            stock_price_data['change_rate'] = change_rate

            stock_price_data_list.append(stock_price_data)

    return fail_logs, stock_price_data_list

def save_stock_price():
    """
    주가 데이터 수집 후 저장

    성공 시 fail_logs와 True 리턴, 실패 시 fail_logs와 False 리턴
    기본 리턴값은 fail_logs, False임
    """
    # 마지막 수집일 조회
    last_collect_date = LastCollectDate.objects.filter(collect_type='stock_price').last()
    if last_collect_date:
        last_collect_date = last_collect_date.collect_date.strftime('%Y%m%d')
    else:
        last_collect_date = datetime(2020, 1, 2).strftime('%Y%m%d')
    
    stock_codes = CorpId.objects.all().values_list('stock_code', flat=True)
    fail_logs, data_list = _collect_stock_price(stock_codes, last_collect_date)

    if data_list:
        # 데이터 중복저장 방지
        for data in data_list:
            if not StockPrice.objects.filter(Q(corp_id=data['corp_id']) & Q(trade_date=data['trade_date'])).exists():
                StockPrice.objects.create(
                    corp_id=data['corp_id'],
                    open_price=data['open_price'],
                    high_price=data['high_price'],
                    low_price=data['low_price'],
                    close_price=data['close_price'],
                    trade_date=data['trade_date'],
                    total_stock=data['total_stock'],
                    market_capitalization=data['market_capitalization'],
                    trade_quantity=data['trade_quantity'],
                    trade_price=data['trade_price'],
                    change_price=data['change_price'],
                    change_rate=data['change_rate'],
                )
            
        return fail_logs, True
        
    return fail_logs, False