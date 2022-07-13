import time
import os

import requests
import re

import logging
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

from . import xmlInterface

logger = logging.getLogger(__name__)

def sync_rep(web_link: str) -> dict:
    logger.info(f'web_link: {web_link}')
    link_to_sync = f'{web_link}/rk7api/v1/forcesyncrefs.xml'
    check_conn = check_conn_to_main_server(web_link)
    logger.info(f'check_conn: {check_conn}')
    result_sync_rep = dict()
    result_sync_rep['web_link'] = web_link
    if check_conn['resume']:
        try:
            requests.get(link_to_sync, verify=False, timeout=3)
            result_sync_rep['status'] = 'In Progress'
        except requests.exceptions.RequestException:
            result_sync_rep['status'] = 'Error'
    else:
        result_sync_rep['status'] = check_conn['status']

    return result_sync_rep


def check_conn_to_main_server(web_link: str) -> dict:
    conn_link = f'{web_link}/Connects'
    result_dict = dict()
    try:
        response = requests.get(conn_link, verify=False, timeout=3)
        soup = BeautifulSoup(response.text, 'lxml')
        check_list = ['REF_TRANSIT', 'RS_REF_TRANSIT', 'CENTER', 'TRANSIT', 'FZ_REF_TRANSIT_764']
        exist_conn = ''
        for check in check_list:
            exist_conn = soup.find_all(string=re.compile(check))
        if exist_conn != '':
            result_dict['status'] = 'Транзит найден'
            result_dict['resume'] = True
        else:
            result_dict['status'] = 'Нет соединеня с транзитом'
            result_dict['resume'] = False

    except requests.exceptions.RequestException:
        result_dict['status'] = 'Connection_Error'
        result_dict['resume'] = False

    return result_dict


def get_rest_info_by_code(rest_code: str) -> dict:
    rest_info = dict()
    path_to_file = os.getcwd() + '/services/rest.xml'
    with open(path_to_file, 'r', encoding='UTF-8') as reference:
        reference_data = reference.read()

    root = ET.fromstring(reference_data)
    try:
        item = root.find(f"RK7Reference/Items/*[@Code='{rest_code}']")
        rest_info['rest_name'] = item.attrib['Name']
        rest_info['code'] = item.attrib['Code']
        rest_info['ip'] = item.attrib['genIP_REP_SRV']
        rest_info['web_link'] = f"https://{item.attrib['genIP_REP_SRV']}:9000"
        rest_info['founded'] = True
    except AttributeError:
        rest_info['founded'] = False

    return rest_info


def get_all_rest_info(owner: str) -> list:
    restaurants = list()
    path_to_file = os.getcwd() + '/services/rest.xml'
    with open(path_to_file, 'r', encoding='UTF-8') as reference:
        reference_data = reference.read()

    root = ET.fromstring(reference_data)
    if owner == 'all':
        items = root.findall(f"RK7Reference/Items/Item")
        for item in items:
            rest_ip = item.attrib['genIP_REP_SRV']
            if rest_ip == '':
                continue
            restaurants.append(dict(name=item.attrib['Name'],
                                    code=item.attrib['Code'],
                                    ip=rest_ip,
                                    web_link=f"https://{item.attrib['genIP_REP_SRV']}:9000"
                                    ))
    else:
        items = root.findall(f"RK7Reference/Items/*[@Owner='{owner}']")
        for item in items:
            rest_ip = item.attrib['genIP_REP_SRV']
            if rest_ip == '':
                continue
            restaurants.append(dict(name=item.attrib['Name'],
                                    code=item.attrib['Code'],
                                    ip=rest_ip,
                                    web_link=f"https://{item.attrib['genIP_REP_SRV']}:9000"
                                    ))

    return restaurants


def check_sync_status(list_info) -> bool:
    web_link = list_info['web_link']
    rep_ref_link = f'{web_link}/References'
    sync_done = False
    count = 1
    while not sync_done:
        time.sleep(5)
        if count == 120:
            break
        logger.info(f'{count}: Старт проверки процесса синхронизации {web_link}')
        try:
            response = requests.get(rep_ref_link, verify=False, timeout=3)
            soup = BeautifulSoup(response.text, 'lxml')
            in_progress = soup.find_all(string=re.compile('in progress'))
            sync_done = False if in_progress else True
            count = count + 1
        except requests.exceptions.RequestException:
            logger.info('Веб морда не ответила')

    return sync_done


def generated_links_to_sync(tranzit_owners: list) -> list:
    tranzit_port_dict = dict(yum=['9001', '9002', '9003', '9004'],
                             irb=['9001', '9002', '9003', '9004', '9005', '9006', '9007',
                                  '9008', '9009', '9010', '9011', '9012', '9013', '9014'],
                             fz=['19401', '19402', '19403', '19404', '19405', '19406', '19407', 
                                 '19408', '19409', '19410', '19411', '19412', '19413'])
    list_links_to_sync = list()
    for owner in tranzit_owners:
        for tranzit_port in tranzit_port_dict[owner]:
            if owner == 'yum':
                list_links_to_sync.append(f"https://192.168.221.24:{tranzit_port}")

            if owner == 'irb':
                list_links_to_sync.append(f"https://10.200.103.223:{tranzit_port}")

            if owner == 'fz':
                list_links_to_sync.append(f"https://95.181.206.172:{tranzit_port}")
    
    return list_links_to_sync

def found_rest_in_ref(rest_code: int):
    """Поиск ресторана на самих справочниках"""
    logger.info('Ищу информацию по ресторану на справочниках')
    
    logger.info('Формирую XML запрос')
    params_for_query = {'values':{'OnlyActive': '1', 'WithMacroProp': '1'}, 'propfilters': [{'Code': str(rest_code), 'type': 'Value'}]}

    xml_for_send = xmlInterface.generate_getxml_for_interface('GetRefData', 'Restaurants', params_for_query)
    logger.info('Сформировал xml запрос. Отправляю')

    response = xmlInterface.send_request_to_interface(xml_for_send)
    
    result = None
    if response is not None and response.status_code == 200:
        result = xmlInterface.parse_xml_response_for_restaurant(response.text)
    
    return result

