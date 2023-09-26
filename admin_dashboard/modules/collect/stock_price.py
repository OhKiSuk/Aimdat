"""
@created at 2023.04.04
@author cslee in Aimdat Team

@modified at 2023.09.14
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
    Max,
    Q
)
from django.db.models.functions import Cast
from requests import (
    ConnectionError, 
    ConnectTimeout, 
    Timeout,
    RequestException
)
from requests.adapters import (
    HTTPAdapter,
    Retry
)
from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice
import xml.etree.ElementTree as ET
from ..api_error.open_api_error import check_open_api_errors

LOGGER = logging.getLogger(__name__)

def _collect_stock_price(stock_codes):
    """
    주가 정보가 수집된 적이 없는 신규 기업 종목의 주가 수집

    공공데이터포털 금융위원회_주식시세정보 중 주식시세 API 사용
    """
    url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo'

    for stock_code in stock_codes:
        try:
            last_trade_date = StockPrice.objects.filter(corp_id__stock_code=stock_code).annotate(
                date_field=Cast(F('trade_date'), output_field=DateField())).latest('date_field').trade_date

            beginBasDt = datetime.strptime(last_trade_date, '%Y-%m-%d').strftime('%Y%m%d')
        except:
            beginBasDt = '20200102'

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
            with requests.Session() as session:
                connect = 100
                read = 50
                backoff_factor = 0.5
                RETRY_AFTER_STATUS_CODES = (400, 403, 500, 503)

                retry = Retry(
                    total=(connect + read),
                    connect=connect,
                    read=read,
                    backoff_factor=backoff_factor,
                    status_forcelist=RETRY_AFTER_STATUS_CODES,
                )

                adaptor = HTTPAdapter(max_retries=retry)
                session.mount("http://", adaptor)
                session.mount("https://", adaptor)

                response = session.get(url=url, params=params)
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
            return False
        elif response.status_code == 500:
            LOGGER.error('[A305] 주가 API 에러. {}'.format(str(stock_code)))
            return False
                
        try:
            response_to_json = response.json()
        except ValueError:
            # OpenAPI 로깅
            root = ET.fromstring(response.text)
            reason_code = root.find('.//returnReasonCode').text
            check_open_api_errors(reason_code)
            continue

        dict_list = response_to_json['response']['body']['items']['item']

        basDt, clpr, vs, fltRt, mkp, hipr, lopr, trqu, trPrc, lstgStCnt, mrktTotAmt = \
        'basDt', 'clpr', 'vs', 'fltRt', 'mkp', 'hipr', 'lopr', 'trqu', 'trPrc', 'lstgStCnt', 'mrktTotAmt'

        if len(dict_list) < 1:
            # A306 로깅
            LOGGER.error('[A306] 주가 정보가 수집되지 않은 종목. {}'.format(str(stock_code)))
            continue
        
        for x in dict_list:
            trade_date = datetime.strptime(x[basDt], '%Y%m%d').strftime('%Y-%m-%d')
            tmp = [x[mkp], x[hipr], x[lopr], x[clpr], x[lstgStCnt], x[mrktTotAmt], x[trqu], x[trPrc], x[vs], x[fltRt]]

            # Decimal Type으로 변환
            tmp = [Decimal(str(x)).quantize(Decimal('0.' + '0'*6), rounding=ROUND_DOWN) for x in tmp]
            open_price, high_price, low_price, close_price, total_stock, market_capitalization, trade_quantity, trade_price, change_price, change_rate = tmp

            if not StockPrice.objects.filter(Q(corp_id__exact=CorpId.objects.get(stock_code=stock_code)) & Q(trade_date__exact=trade_date)).exists():
                StockPrice.objects.create(
                    corp_id=CorpId.objects.get(stock_code=stock_code),
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

    return True

def save_stock_price(tab):
    """
    주가 데이터 수집 후 저장

    성공 시 True 리턴, 실패 시 False 리턴, 기본 리턴값은 False임
    """
    stock_codes = []

    if tab == 'all_collect':
        stock_codes = CorpId.objects.all().order_by('corp_name').values_list('stock_code', flat=True)
    elif tab == 'not_collected':
        lastest_date = StockPrice.objects.aggregate(lastest_date=Max('trade_date'))['lastest_date'] # 전체 수집 데이터 중 최근 거래일
        
        stock_codes = []
        for stock_code in CorpId.objects.all().order_by('corp_name').values_list('stock_code', flat=True):
            stock_lastest_date = StockPrice.objects.filter(corp_id_id__stock_code=stock_code).aggregate(lastest_trade_date=Max('trade_date'))['lastest_trade_date'] # 기업의 최근 수집일

            if lastest_date != stock_lastest_date:
                stock_codes.append(stock_code)

    result = _collect_stock_price(stock_codes)

    return result