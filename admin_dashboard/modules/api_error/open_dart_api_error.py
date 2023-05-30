"""
@created at 2023.05.17
@author OKS in Aimdat Team

@modified at 2023.05.25
@author JSU in Aimdat Team
"""

import logging

LOGGER = logging.getLogger(__name__)

def check_open_dart_api_error(status):
    """
    OpenDartAPI에서 발생한 에러 확인 및 반환

    code | error message                                    | description
    〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓〓
    010  | SERVICE_KEY_IS_NOT_REGISTERED_ERROR              | 등록되지 않은 키입니다.
    011  | SERVICE_KEY_CAN_NOT_USE_ERROR                    | 사용할 수 없는 키입니다.
         |                                                  | 오픈API에 등록되었으나, 일시적으로 사용 중지된 키를 통하여 검색하는 경우 발생합니다.
    012  | SERVICE_ACCESS_DENIED_ERROR                      | 접근할 수 없는 IP입니다.
    013  | DATA_NOT_FOUND_ERROR                             | 조회된 데이터가 없습니다.
    014  | FILE_DOES_NOT_EXIST_ERROR                        | 파일이 존재하지 않습니다.
    020  | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | 요청 제한(최대 10,000건)을 초과하였습니다.
    021  | LIMITED_NUMBER_OF_SEARCH_CORP_ERROR              | 조회 가능한 회사 개수가 초과하였습니다.(최대 100건)
    100  | INAPPROPRIATE_FIELD_VALUE_ERROR                  | 필드의 부적절한 값입니다. 필드 설명에 없는 값을 사용한 경우에 발생하는 메시지입니다.
    101  | INAPPROPRIATE_ACCESS_ERROR                       | 부적절한 접근입니다.
    800  | SYSTEM_INSPECTION_ERROR                          | 시스템 점검으로 인한 서비스가 중지 중입니다.
    900  | UNKNOWN_ERROR                                    | 정의되지 않은 오류가 발생하였습니다.
    901  | SERVICE_KEY_EXPIRED_ERROR                        | 사용자 계정의 개인정보 보유기간이 만료되어 사용할 수 없는 키입니다.
    """
    if status == '010':
        LOGGER.error('[O111] 등록되지 않은 서비스키')

    elif status == '011' or status == '901':
        LOGGER.error('[O112] 사용할 수 없는 서비스키')

    elif status == '012':
        LOGGER.error('[O121] IP 차단됨')

    elif status == '013':
        LOGGER.error('[O122] 조회된 데이터 없음')

    elif status == '014':
        LOGGER.error('[O123] 파일이 존재하지 않음')

    elif status == '020':
        LOGGER.error('[O132] 요청제한횟수 초과')

    elif status == '021':
        LOGGER.error('[O133] 조회제한횟수 초과')

    elif status == '100':
        LOGGER.error('[O131] 잘못된 파라미터')

    elif status == '101':
        LOGGER.error('[O124] 부적절한 접근 시도')

    elif status == '800' or status == '900':
        LOGGER.error('[O100] DART API 에러 ')