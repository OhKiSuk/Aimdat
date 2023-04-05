"""
@modified at 2023.04.05
@author cslee in Aimdat Team
"""
import os
import pandas as pd
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

dir_collect = os.path.dirname(__file__)
dir_modules = os.path.dirname(dir_collect)
dir_admin_dashboard = os.path.dirname(dir_modules)
dir_aimdat = os.path.dirname(dir_admin_dashboard)
sys.path.append(dir_aimdat)

from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo

def _crawl_corp_list_files(year, crawl_time=2, download_time=5):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    # download 상장법인목록.xls
    url = 'https://kind.krx.co.kr/corpgeneral/corpList.do?method=loadInitPage'
    driver.get(url)
    time.sleep(crawl_time)
    btn_download = driver.find_element(By.XPATH, "//a[@title='EXCEL']")
    btn_download.click()
    time.sleep(crawl_time)

    # download opendart xbrl list
    year = 2022
    url = 'https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do'
    driver.get(url)
    time.sleep(crawl_time)
    btn_year = driver.find_element(By.XPATH, "//a[@title={}]".format(year))
    btn_year.click()
    time.sleep(crawl_time)
    btn_1Q_BS = driver.find_element(By.XPATH, "//a[@title='{} 1분기보고서 재무상태표 다운로드']".format(year))
    # btn_2Q_BS = driver.find_element(By.XPATH, "//a[@title='{} 반기보고서 재무상태표 다운로드']".format(year))
    # btn_3Q_BS = driver.find_element(By.XPATH, "//a[@title='{} 3분기보고서 재무상태표 다운로드']".format(year))
    # btn_4Q_BS = driver.find_element(By.XPATH, "//a[@title='{} 사업보고서 재무상태표 다운로드']".format(year))
    btn_1Q_BS.click()
    time.sleep(crawl_time)

    time.sleep(download_time)  

def _unzip(path, year, operate_system):
    # unzip
    zip_name = ""
    for f_name in os.listdir(path):
        if f_name.startswith(str(year)) & f_name.endswith('.zip'):
            zip_name = f_name
            break
    zip_path = path+'\\'+zip_name
    
    folder_name = zip_name[:-4]
    folder_path = path+'\\'+folder_name
    if operate_system == 'win':
        os.system("powershell.exe Expand-Archive -Force {} {}".format(zip_path, folder_path)) # window
    elif operate_system == 'linux':
        os.system("unzip {}".format(zip_path)) # linux

    time.sleep(1)
    txt_name = ''
    for f_name in os.listdir(folder_path):
        if f_name.startswith(str(year)):
            txt_name = f_name
            break
    txt_path = folder_path+'\\'+txt_name
    return txt_path, zip_path, folder_path

def _save_id_and_info(df, corp_list, is_crawl):
    
    for name in corp_list['회사명']:
        ret = df.loc[df['회사명']==name, ['회사명', '종목코드', '업종', '결산월', '대표자명', '홈페이지']]
        ret = ret.values.tolist()
        corp_name, stock_code, corp_sectors, corp_settlement_month, corp_ceo_name, corp_homepage_url = ret[0]
        stock_code = str(stock_code)
        n = len(stock_code)
        stock_code = '0'*(6-n)+stock_code
        try:
            id_data = CorpId.objects.get(stock_code=stock_code)
            id_data.corp_name = corp_name
            id_data.corp_sectors = corp_sectors
            id_data.stock_code = stock_code     
            id_data.is_crawl = is_crawl
            id_data.save()
            try:
                info_data = CorpInfo.objects.get(corp_id=id_data.pk)
                info_data.corp_ceo_name = corp_ceo_name
                info_data.corp_homepage_url = corp_homepage_url
                info_data.corp_settlement_month = corp_settlement_month   
            except CorpInfo.DoesNotExist:
                info_data = CorpInfo(
                corp_id = id_data,
                corp_ceo_name = corp_ceo_name,
                corp_homepage_url = corp_homepage_url,
                corp_settlement_month = corp_settlement_month,
                corp_summary = None
            )
        except CorpId.DoesNotExist:
            id_data = CorpId(  # create
                corp_name = corp_name,
                corp_sectors = corp_sectors,
                stock_code = stock_code,
                is_crawl = is_crawl
            )
            id_data.save()
            try:
                info_data = CorpInfo.objects.get(corp_id=id_data.pk)
                info_data.corp_ceo_name = corp_ceo_name
                info_data.corp_homepage_url = corp_homepage_url
                info_data.corp_settlement_month = corp_settlement_month   
            except CorpInfo.DoesNotExist:
                info_data = CorpInfo(
                corp_id = id_data,
                corp_ceo_name = corp_ceo_name,
                corp_homepage_url = corp_homepage_url,
                corp_settlement_month = corp_settlement_month,
                corp_summary = None
            )
        info_data.save()

def _delete_id(corp_list):
    for name in corp_list['회사명']:
        try:
            target = CorpId.objects.get(corp_name=name)
            target.delete()
        except CorpId.DoesNotExist:
            pass
        
def _remove_file(file_path, operate_system, folder=False):

    if operate_system == 'win':
        if folder:
            os.system('echo y | rd /s {} '.format(file_path))
        else:
            os.system('del {}'.format(file_path)) # window
    elif operate_system == 'linux':
        os.system('rm -rf {}'.format(file_path)) # linux

def collect_corp(year=2022, operate_system='win'):
    _crawl_corp_list_files(year)
    path = r'C:\Users\80ckd\Downloads' 
    fname = '상장법인목록.xls'
    file_krx_list = path +'\\'+ fname

    file_dart_fs_list, zip_path, folder_path = _unzip(path, year, operate_system) 
    # read file
    df1 = pd.read_html(file_krx_list)[0]
    df1_corp_name = df1['회사명'].unique()
    df1_corp_name = pd.DataFrame(df1_corp_name)

    df2 = pd.read_csv(file_dart_fs_list, sep='\t', encoding='cp949')
    df2_corp_name = df2['회사명'].unique()
    df2_corp_name = pd.DataFrame(df2_corp_name)

    # merge
    df3 = pd.merge(df1_corp_name, df2_corp_name, how='outer', indicator=True)
    df3.columns = ['회사명', '_merge']
    
    # crawl list
    X = df3[ df3['_merge'] == 'left_only']
    _save_id_and_info(df1, X, True) 
    # Can use API list
    X = df3[ df3['_merge'] == 'both']
    _save_id_and_info(df1, X, False) 
    # 상장폐지 list -> db 제거
    X = df3[ df3['_merge'] == 'right_only'] 
    _delete_id(X)
    # 다사용한 파일 삭제
    _remove_file(file_krx_list, operate_system)
    _remove_file(zip_path, operate_system)
    _remove_file(folder_path, operate_system, folder=True)

    