"""Функции для работы с xml интерфейсом R-Keeper
   Глобальные переменные которые обязательны:
   XML_LINK - сылка на адрес интерфейса
   XML_LOGIN - логин для авторизации на интерфейсе для выполнения запроса
   XML_PASSWORD - пароль для авторизации на интерфейсе для выполнения запроса
"""
import requests
import urllib3
from  xml.etree import ElementTree as ET
import env_config as config
from requests.auth import HTTPBasicAuth

import logging
logger = logging.getLogger(__name__)

logger.info(config.XML_LOGIN)
logger.info(config.XML_PASSWORD)
logger.info(config.XML_LINK)
# создание xml для get запроса на интерфейс
def generate_getxml_for_interface(cmd:str, collection:str, params:dict, nesting = 0) -> str:
    """
    ref_cmd - команда запроса к справочникам.
    collection - имя коллекции справочника для запроса
    params - dict с настройками запроса, основные параметры (values) и дополнительные (propfilters)
    nesting - вложенность пропфильтров. // TODO сделать тест
    например: {'values':{'OnlyActive': 1, 'WithMacroProp': 1}, 'propfilters': [{'Owner':'Ям', 'type': 'Substring'}, {'Code': '8702', type: 'Values'}]}
    """
    req_values = params.get('values')
    req_propfilters = params.get('propfilters')
    
    logger.info(req_values)
    logger.info(req_propfilters)

    root = ET.Element("RK7Query")
    rk7cmd = ET.SubElement(root, 'RK7CMD')
    rk7cmd.set('CMD', cmd)
    rk7cmd.set('RefName', collection)

    if req_values is not None:
        for key in req_values:
            rk7cmd.set(key, req_values[key])

    if req_propfilters is not None:
        propfilters_count = len(req_propfilters)
        prop_filters = ET.SubElement(rk7cmd, 'PROPFILTERS')
        if nesting == 0:
            prop_filter = ET.SubElement(prop_filters, 'PROPFILTER') 

        if propfilters_count > 1:
            i = 0
            while i < propfilters_count:
                i+=1
                if nesting == 1:
                    sub_prop_filter = ET.SubElement(prop_filters, 'PROPFILTER')  
                else:
                    sub_prop_filter = ET.SubElement(prop_filter, 'PROPFILTER')     
                
                for key in req_propfilters[i - 1]:
                    if key != 'type':
                        sub_prop_filter.set('Name', key)
                        key_value = req_propfilters[i - 1][key]
                    else:    
                        sub_prop_filter.set(req_propfilters[i - 1][key], key_value)
        else:
            count = 0    
            for key in req_propfilters[count]:
                if key != 'type':
                    prop_filter.set('Name', key)
                    key_value = req_propfilters[count][key]
                else:    
                    prop_filter.set(req_propfilters[count][key], key_value)
    
    xml_to_str = ET.tostring(root, 'utf-8')
    xml_doc = '<?xml version="1.0" encoding="UTF-8"?>' + xml_to_str.decode('utf-8')
    logger.info(xml_doc)
    return xml_doc


# отправка запроса на интерфейс
def send_request_to_interface(xml_request):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {'Content-Type': 'application/xml'}
    try:
        password_xml = f'{config.XML_PASSWORD}'
        print(password_xml)
        request_response = requests.post(config.XML_LINK, data=xml_request, headers=headers,
                                         verify=False, auth=HTTPBasicAuth('GetREF', r'Hm:N)Z27'))
        logger.info(config.XML_LINK)
        logger.info(request_response.text)
        if request_response.status_code == 401:
            print('Не верный логин или пароль')                             
        
        return request_response
    except requests.exceptions.MissingSchema:
        print('Не задан адрес интерфейса')

    except requests.exceptions.ConnectionError:
        print('Нет ответа от интерфейса')        


# парсинг xml ответа от интерфейса в случаи успеха
def parse_xml_response_for_restaurant(xml: str):
    
    tree = ET.fromstring(xml)
    item = tree.find('RK7Reference/Items/Item')

    try:
        rest_ident = item.attrib['Ident']
        rest_name = item.attrib['Name']
        rest_code = item.attrib['Code']
        rest_region = item.attrib['Region']
        rest_owner = item.attrib['Owner'].replace('\"', '').replace('ООО ', '')
        rest_service_company = item.attrib['genService_company']
        rest_ip = item.attrib['genIP_REP_SRV']
            
        rests_info = {
                    'ident': int(rest_ident),
                    'name': rest_name,
                    'code': int(rest_code),
                    'region': int(rest_region),
                    'owner': rest_owner,
                    'service_company': rest_service_company,
                    'ip': rest_ip
                }
    except AttributeError:
        return None
    
    return rests_info        
    
