"""
@created at 2023.03.24
@author cslee in Aimdat Team

@modified at 2023.05.17
@author OKS in Aimdat Team
"""
import datetime
import requests
import retry

from config.settings.base import get_secret
from services.models.corp_id import CorpId
from ..api_error.open_api_error import check_open_api_errors

@retry.retry(exceptions=TimeoutError, tries=10, delay=3)
def _collect_corp_id():
    """
    기업 식별자 정보 수집
    """
    # 수집 날짜 지정(한국 기준)
    date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))) - datetime.timedelta(days=1)

    # 평일, 주말 구분(0 ~ 4: 평일, 5: 토요일, 6: 일요일)
    if date.weekday() == 5:
        likeBasDt = date - datetime.timedelta(days=1)
    elif date.weekday() == 6:
        likeBasDt = date - datetime.timedelta(days=2)
    else:
        likeBasDt = date

    url = 'https://apis.data.go.kr/1160100/service/GetKrxListedInfoService/getItemInfo'
    params = {
        'serviceKey': get_secret('data_portal_key'),
        'numOfRows': 100_000,
        'pageNo': 1,
        'resultType': 'json',
        'basDt': likeBasDt.strftime('%Y%m%d')
    }
    
    response = requests.get(url, params=params, verify=False)

    fail_logs = []
    try:
        response_to_json = response.json()
    except ValueError:
        # OpenAPI 에러처리
        log = check_open_api_errors(response)
        fail_logs.append(log)

    corp_list = response_to_json['response']['body']['items']['item']

    return corp_list, fail_logs

def save_corp_id():
    """
    기업 식별자 저장

    성공 시 fail_logs와 True 리턴, 실패 시 fail_logs와 False 리턴
    기본 리턴값은 fail_logs, False임
    """
    corp_list, fail_logs = _collect_corp_id()
    
    if len(corp_list) > 0:
        for corp in corp_list:
            # 중복 저장 방지
            if not CorpId.objects.filter(stock_code=corp['srtnCd'][1:]).exists():
                CorpId.objects.create(
                    corp_name=corp['itmsNm'],
                    corp_country='대한민국',
                    corp_market=corp['mrktCtg'],
                    corp_isin=corp['isinCd'],
                    stock_code=corp['srtnCd'][1:]
                )
        return fail_logs, True
    else:
        fail_logs.append(
            {
                'error_code': '',
                'error_rank': 'info',
                'error_detail': 'NO_RESULT_FOUND_AT_COLLECT_CORP_ID',
                'error_time': datetime.datetime.now()
            }
        )
    
    return fail_logs, False