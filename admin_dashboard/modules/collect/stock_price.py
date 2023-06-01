"""
@created at 2023.04.04
@author cslee in Aimdat Team

@modified at 2023.06.01
@author OKS in Aimdat Team
"""
import logging
import requests
import time

from datetime import datetime
from decimal import (
    Decimal,
    ROUND_DOWN
)

from config.settings.base import get_secret
from django.db.models import (
    DateField,
    F,
    Q
)
from django.db.models.functions import Cast
from requests import ConnectionError, ConnectTimeout, Timeout, RequestException
from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice
from ..api_error.open_api_error import check_open_api_errors

LOGGER = logging.getLogger(__name__)

def _check_is_new(stock_code):
    """
    주가정보를 처음 수집하는 기업 구분
    """
    corp_id = CorpId.objects.get(stock_code=stock_code).id
    if StockPrice.objects.filter(corp_id__id=corp_id).exists():
        return False
    else:
        # A302 로깅
        LOGGER.info('[A302] 새로운 주가정보가 수집됨. {}'.format(stock_code))
        return True
    
def _collect_stock_price(stock_codes):
    """
    주가 정보가 수집된 적이 없는 신규 기업 종목의 주가 수집

    공공데이터포털 금융위원회_주식시세정보 중 주식시세 API 사용
    """
    url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo'

    stock_price_data_list = []
    for stock_code in stock_codes:
        is_new = _check_is_new(stock_code)

        if is_new:
            beginBasDt = '20200102'
        else:
            last_trade_date = StockPrice.objects.filter(corp_id__stock_code=stock_code).annotate(
                date_field=Cast(F('trade_date'), output_field=DateField())).latest('date_field').trade_date

            beginBasDt = datetime.strptime(last_trade_date, '%Y-%m-%d').strftime('%Y%m%d') 

        params = {
            'serviceKey':get_secret('data_portal_key'), 
            'numOfRows':10000, 
            'pageNo':1, 
            'resultType':'json', 
            'beginBasDt':beginBasDt,
            'likeSrtnCd':stock_code
        }

        # API 호출 로깅
        try:
            response = requests.get(url, params=params, verify=False)
        except ConnectTimeout:
            LOGGER.error('[A013] Requests 연결 타임아웃 에러')
        except ConnectionError:
            LOGGER.error('[A012] Requests 연결 에러')
        except Timeout:
            LOGGER.error('[A011] Requests 타임아웃 에러')
        except RequestException:
            LOGGER.error('[A010] Requests 범용 에러')

        time.sleep(0.5)

        if response.status_code == 422:
            LOGGER.error('[A304] 주가 API 파라미터 에러. {}'.format(str(stock_code)))
        elif response.status_code == 500:
            LOGGER.error('[A305] 주가 API 에러. {}'.format(str(stock_code)))
                
        try:
            response_to_json = response.json()
        except ValueError:
            # OpenAPI 로깅
            check_open_api_errors(response)
            break

        dict_list = response_to_json['response']['body']['items']['item']

        basDt, clpr, vs, fltRt, mkp, hipr, lopr, trqu, trPrc, lstgStCnt, mrktTotAmt = \
        'basDt', 'clpr', 'vs', 'fltRt', 'mkp', 'hipr', 'lopr', 'trqu', 'trPrc', 'lstgStCnt', 'mrktTotAmt'

        if len(dict_list) < 1:
            # A303 로깅
            LOGGER.error('[A303] 주가 정보가 정상 수집되지 않음. {}'.format(str(stock_code)))
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

    return stock_price_data_list

def save_stock_price():
    """
    주가 데이터 수집 후 저장

    성공 시 True 리턴, 실패 시 False 리턴, 기본 리턴값은 False임
    """    
    stock_codes = CorpId.objects.all().values_list('stock_code', flat=True)
    data_list = _collect_stock_price(stock_codes)

    if data_list:
        # 데이터 중복저장 방지
        for data in data_list:
            if not StockPrice.objects.filter(Q(corp_id__exact=data['corp_id']) & Q(trade_date__exact=data['trade_date'])).exists():
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
            
        return True
        
    return False
