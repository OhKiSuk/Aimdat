"""
@created at 2023.03.24
@author cslee in Aimdat Team

@modified at 2023.06.15
@author JSU in Aimdat Team
"""
import datetime
import logging
import requests

from config.settings.base import get_secret
from django.db.models import Q
from requests import ConnectionError, ConnectTimeout, Timeout, RequestException
from services.models.corp_id import CorpId
from ..api_error.open_api_error import check_open_api_errors

LOGGER = logging.getLogger(__name__)

def _collect_corp_id():
    """
    기업 식별자 정보 수집
    """
    # 수집 날짜 지정(한국 기준)
    BasDt = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) - datetime.timedelta(days=1)

    # 최근 일주일 안에 업데이트 된 상장 목록 획득
    for _ in range(7):
        url = 'https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo'
        params = {
            'serviceKey': get_secret('data_portal_key'),
            'numOfRows': 100000,
            'pageNo': 1,
            'resultType': 'json',
            'basDt': BasDt.strftime('%Y%m%d')
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
        
        try:
            response_to_json = response.json()
            
            if int(response_to_json['response']['body']['totalCount']) == 0:
                BasDt = BasDt - datetime.timedelta(days=1)
                continue
            else:
                corp_list = response_to_json['response']['body']['items']['item']
                break
        except ValueError:
            # OpenAPI 로깅
            check_open_api_errors(response)
            break

    return corp_list

def save_corp_id():
    """
    기업 식별자 저장

    성공 시 True 리턴, 실패 시 False 리턴, 기본 리턴값은 False임
    """
    corp_list = _collect_corp_id()
    
    if len(corp_list) > 0:
        for corp in corp_list:

            if CorpId.objects.filter(Q(corp_name__exact=corp['itmsNm']) | Q(stock_code__exact=corp['srtnCd'][1:]) | Q(corp_isin__exact=corp['isinCd'])).exists():
                CorpId.objects.filter(Q(corp_name__exact=corp['itmsNm']) | Q(stock_code__exact=corp['srtnCd'][1:]) | Q(corp_isin__exact=corp['isinCd'])).update(
                    corp_name = corp['itmsNm'],
                    corp_isin = corp['isinCd'],
                    stock_code = corp['srtnCd'][1:],
                    base_date = datetime.datetime.strptime(corp['basDt'], '%Y%m%d').strftime('%Y-%m-%d')
                )
            else:
                CorpId.objects.create(
                    corp_name=corp['itmsNm'],
                    corp_country='대한민국',
                    corp_market=corp['mrktCtg'],
                    corp_isin=corp['isinCd'],
                    stock_code=corp['srtnCd'][1:],
                    base_date=datetime.datetime.strptime(corp['basDt'], '%Y%m%d').strftime('%Y-%m-%d')
                )

        return True
    
    return False