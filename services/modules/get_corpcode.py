"""
@created at 2023.04.09
@author JSU in Aimdat Team
"""
import json
import xml.etree.ElementTree as ET
import zipfile

import requests
from django.apps import apps

from config.settings.base import get_secret


def get_corpcode(self):
     # corp_code xml 파일 가져오기
    app_config = apps.get_app_config('services')
    url = 'https://opendart.fss.or.kr/api/corpCode.xml'
    api_key = get_secret('dart_api_key')

    file = requests.get(url, params={'crtfc_key': api_key})
    open(app_config.path + '/corpcode.zip', 'wb').write(file.content)

    with zipfile.ZipFile(app_config.path + '/corpcode.zip', 'r') as zip_file:
        zip_file.extractall(app_config.path)

    # stock_code와 corp_code 값 dict 형태로 저장
    tree = ET.parse(app_config.path + '/CORPCODE.xml')
    root = tree.getroot()
    stock_code = []
    corp_code = []

    for list_element in root.findall("./list[stock_code != ' ']"):
        stock_code.append(list_element.find('stock_code').text)
        corp_code.append(list_element.find('corp_code').text)

    result = dict(zip(stock_code, corp_code))

    with open(app_config.path + '/corp_code.json', 'w') as f:
        json.dump(result, f)