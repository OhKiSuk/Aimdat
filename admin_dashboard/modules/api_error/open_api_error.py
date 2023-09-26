"""
@created at 2023.05.17
@author OKS in Aimdat Team

@modified at 2023.09.05
@author OKS in Aimdat Team
"""

import logging

LOGGER = logging.getLogger(__name__)

def check_open_api_errors(reason_code):
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
    
    if reason_code == '01' or reason_code == '99':
        LOGGER.error('[O200] 데이터포털 API 에러')

    elif reason_code == '10':
        LOGGER.error('[O231] 잘못된 파라미터')

    elif reason_code == '12':
        LOGGER.error('[O233] 해당 오픈API서비스가 없거나 폐기됨')

    elif reason_code == '20':
        LOGGER.error('[O221] 서비스 접근거부')

    elif reason_code == '22':
        LOGGER.error('[O232] 요청제한횟수 초과')

    elif reason_code == '30':
        LOGGER.error('[O211] 등록되지 않은 서비스키')

    elif reason_code == '31':
        LOGGER.error('[O212] 기한이 만료된 서비스키')

    elif reason_code == '32':
        LOGGER.error('[O222] 등록되지 않은 IP')