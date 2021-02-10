import logging
import os
import time

import requests
import re

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET


def sync_rep(web_link: str) -> dict:
    link_to_sync = f'{web_link}/rk7api/v1/forcesyncrefs.xml'
    check_conn = check_conn_to_main_server(web_link)
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
        rest_info['code'] = item.attrib['Code']
        rest_info['ip'] = item.attrib['genIP_REP_SRV']
        rest_info['web_link'] = f"https://{item.attrib['genIP_REP_SRV']}:9000"
        rest_info['founded'] = True
    except AttributeError:
        rest_info['founded'] = False

    return rest_info


def get_all_rest_info(owner: str) -> list:
    restaurants = list()
    path_to_file = os.getcwd() + '\\services\\rest.xml'
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


def check_sync_status(list_info: list) -> bool:
    web_link = list_info['web_link']
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
            soup = BeautifulSoup(response.text, 'lxml')
            in_progress = soup.find_all(string=re.compile('in progress'))
            sync_done = False if in_progress else True
            count = count + 1
        except requests.exceptions.RequestException:
            logging.info('Веб морда не ответила')

    return sync_done


def generated_links_to_sync(tranzit_owners: list) -> list:
    tranzit_port_dict = dict(yum=['9001', '9002', '9003', '9004'],
                             irb=['5001', '5002', '5003', '5004', '5005', '5006', '5007',
                                  '5008', '5009', '5010', '5011', '5012', '5013'])
    list_links_to_sync = list()
    for owner in tranzit_owners:
        for tranzit_port in tranzit_port_dict[owner]:
            if owner == 'yum':
                list_links_to_sync.append(f"https://192.168.221.24:{tranzit_port}")

            if owner == 'irb':
                list_links_to_sync.append(f"https://10.200.103.223:{tranzit_port}")

    return list_links_to_sync
