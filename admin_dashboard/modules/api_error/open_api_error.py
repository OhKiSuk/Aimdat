"""
@created at 2023.05.17
@author OKS in Aimdat Team
"""
import xml.etree.ElementTree as ET

from datetime import datetime

def check_open_api_errors(response):
    """
    공공데이터포털 OpenAPI 에러 확인 및 반환

    code   | error message                                    | description
    〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓
    1	   | APPLICATION_ERROR	                              | 어플리케이션 에러
    10	   | INVALID_REQUEST_PARAMETER_ERROR	              | 잘못된 요청 파라메터 에러
    12	   | NO_OPENAPI_SERVICE_ERROR	                      | 해당 오픈API서비스가 없거나 폐기됨
    20	   | SERVICE_ACCESS_DENIED_ERROR	                  | 서비스 접근거부
    22	   | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 서비스 요청제한횟수 초과 에러
    30	   | SERVICE_KEY_IS_NOT_REGISTERED_ERROR	          | 등록되지 않은 서비스키
    31	   | DEADLINE_HAS_EXPIRED_ERROR	                      | 기한 만료된 서비스키
    32	   | UNREGISTERED_IP_ERROR	                          | 등록되지 않은 IP
    99	   | UNKNOWN_ERROR	                                  | 기타 에러
    """
    root = ET.fromstring(response.text)
    reason_code = root.find('.//returnReasonCode').text
    
    log = {}
    if reason_code == '1':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] == 'APPLICATION_ERROR'
        log['error_time']= datetime.now()
    elif reason_code == '10':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'INVALID_REQUEST_PARAMETER_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '12':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail']= 'NO_OPENAPI_SERVICE_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '20':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'SERVICE_ACCESS_DENIED_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '22':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '30':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'SERVICE_KEY_IS_NOT_REGISTERED_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '31':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'DEADLINE_HAS_EXPIRED_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '32':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'UNREGISTERED_IP_ERROR'
        log['error_time'] = datetime.now()
    elif reason_code == '99':
        log['error_code'] = ''
        log['error_rank'] = 'info'
        log['error_detail'] = 'UNKNOWN_ERROR'
        log['error_time'] = datetime.now()

    return log