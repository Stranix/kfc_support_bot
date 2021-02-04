import logging
import os
import time

import requests
import re

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET


def sync_rep(web_link: str) -> bool:
    link_to_sync = f'{web_link}/rk7api/v1/forcesyncrefs.xml'
    try:
        requests.get(link_to_sync, verify=False, timeout=3)
        start_sync = True
    except requests.exceptions.RequestException:
        start_sync = False

    return start_sync


def check_conn_to_main_server(conn_link: str) -> dict:
    result_dict = dict()
    try:
        response = requests.get(conn_link, verify=False, timeout=3)
        soup = BeautifulSoup(response.text, 'lxml')
        check_list = ['REF_TRANSIT', 'RS_REF_TRANSIT', 'CENTER', 'TRANSIT']
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
    path_to_file = os.getcwd() + '\\services\\rest.xml'
    with open(path_to_file, 'r', encoding='UTF-8') as reference:
        reference_data = reference.read()

    root = ET.fromstring(reference_data)
    try:
        item = root.find(f"RK7Reference/Items/*[@Code='{rest_code}']")
        rest_info['rest_name'] = item.attrib['Name']
        rest_info['ip'] = item.attrib['genIP_REP_SRV']
        rest_info['web_link'] = f"https://{item.attrib['genIP_REP_SRV']}:9000"
    except AttributeError:
        rest_info['rest_name'] = False

    return rest_info


def get_all_rest_ip() -> list:
    all_restaurants_ip = []
    path_to_file = os.getcwd() + '\\services\\rest.xml'
    with open(path_to_file, 'r', encoding='UTF-8') as reference:
        reference_data = reference.read()

    root = ET.fromstring(reference_data)
    items = root.findall(f"RK7Reference/Items/Item")
    for item in items:
        rest_ip = item.attrib['genIP_REP_SRV']
        if rest_ip == '':
            continue
        web_link = f"https://{item.attrib['genIP_REP_SRV']}:9000"
        all_restaurants_ip.append(web_link)

    return all_restaurants_ip


def check_sync_status(web_link: str) -> bool:
    rep_ref_link = f'{web_link}/References'
    sync_done = False
    count = 1
    while not sync_done:
        time.sleep(5)
        if count == 120:
            break
        logging.info(f'{count}: Старт проверки процесса синхронизации {web_link}')
        try:
            response = requests.get(rep_ref_link, verify=False, timeout=3)
        except requests.exceptions.RequestException:
            logging.info('Веб морда не ответила')

        soup = BeautifulSoup(response.text, 'lxml')
        in_progress = soup.find_all(string=re.compile('in progress'))
        sync_done = False if in_progress else True
        count = count + 1

    return sync_done
