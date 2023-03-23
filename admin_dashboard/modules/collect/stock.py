import requests
import time
import os, sys
import json

dir_collect = os.path.dirname(__file__)
dir_modules = os.path.dirname(dir_collect)
dir_admin_dashboard = os.path.dirname(dir_modules)
dir_aimdat = os.path.dirname(dir_admin_dashboard)
sys.path.append(dir_aimdat)

from services.models.corp_id import CorpId
from services.models.stock_price import StockPrice

def _get_API_corp_list():
    try:
        crawl_list = CorpId.objects.all()
        ret = []
        for i in crawl_list:
            ret.append(i.stock_code)
        return ret
    except CorpId.DoesNotExist:
        print('크롤링을 해야하는 기업 리스트가 존재하지 않습니다.')


def _get_service_key(key_name):
    SECRETS_DIR = os.path.join(dir_aimdat, '.secrets')
    secrets = json.load(open(os.path.join(SECRETS_DIR, 'secrets.json')))
    data_portal_key = 'data_portal_key'
    service_key = secrets[data_portal_key]

    return service_key

def collect_stockPrice():
    url = 'https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo'
    data_portal_key = 'data_portal_key'
    service_key = _get_service_key(data_portal_key)
    corp_list = _get_API_corp_list()
    for stock_code in corp_list:
        params = {'serviceKey':service_key, 'numOfRows':100000000, 'pageNo':1, 'resultType':'json', 'beginBasDt':20200102, 'likeSrtnCd':stock_code}
        try:
            res = requests.get(url, params=params, verify=False)
        except TimeoutError:
            time.sleep(60)
            res = requests.get(url, params=params, verify=False)
        while(1):
            if res.status_code != 200:
                res = requests.get(url, params=params, verify=False)
            else:
                break
        res_data = res.json()
        dict_list = res_data['response']['body']['items']['item']
 
        basDt, srtnCd, isinCd, itmsNm, mrktCtg, clpr, vs, fltRt, mkp, hipr, lopr, trqu, trPrc, lstgStCnt, mrktTotAmt = \
        'basDt', 'srtnCd', 'isinCd', 'itmsNm', 'mrktCtg', 'clpr', 'vs', 'fltRt', 'mkp', 'hipr', 'lopr', 'trqu', 'trPrc', 'lstgStCnt', 'mrktTotAmt'

        # corpID
        tmp = dict_list[0]
        stock_code = tmp[srtnCd]
        corp_name = tmp[itmsNm]
        corp_isin = tmp[isinCd]
        corp_market = tmp[mrktCtg]
        corp_country = corp_isin[:2]

        try:
            id_data = CorpId.objects.get(stock_code=stock_code)
            id_data.corp_isin = corp_isin
            id_data.corp_market = corp_market
            id_data.corp_country = corp_country
        except CorpId.DoesNotExist:
            continue
        id_data.save()

        # stockPrice
        for x in dict_list:
            open_price = x[mkp]
            high_price = x[hipr]
            low_price = x[lopr]
            close_price = x[clpr]
            trading_date = x[basDt]
            total_stock = x[lstgStCnt]
            market_capitalization = x[mrktTotAmt]
            trade_quantity = x[trqu]
            trade_price = x[trPrc]
            change_price = x[vs]
            change_rate = x[fltRt]

            try:
                sp_data = StockPrice.objects.get(trading_date=trading_date)
                continue
            except StockPrice.DoesNotExist:
                sp_data = StockPrice(
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    trading_date=trading_date,
                    total_stock=total_stock,
                    market_capitalization=market_capitalization,
                    trade_quantity=trade_quantity,
                    trade_price=trade_price,
                    change_price=change_price,
                    change_rate=change_rate
                )
            sp_data.save()