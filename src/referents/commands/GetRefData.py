import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger('xml_interface')


def get_ref_data(collections: str, query: dict, nesting=False) -> str:
    """Генерация XML файла для команды GetRefData

    @collections: название коллекции с которой работаем
    @query: словарь запроса, параметры запроса

    Пример query:

    {'propfilters':{'Name': 'AltName', 'Substring': alt_name},
    'cmd_param': {'OnlyActive':'1', 'PropMask': r'{Code, AltName}'}
    }
    """

    root = ET.Element("RK7Query")
    rk7cmd = ET.SubElement(root, 'RK7CMD')
    rk7cmd.set('CMD', 'GetRefData')
    rk7cmd.set('RefName', collections)
    for key, value in query['cmd_param'].items():
        rk7cmd.set(key, value)

    if query.get('propfilters'):
        propfilters = ET.SubElement(rk7cmd, 'PROPFILTERS')
        query_props = query['propfilters']
        if not nesting:
            propfilter = ET.SubElement(propfilters, 'PROPFILTER')
            for k, v in query_props.items():
                propfilter.set(k, v)

    xml_to_str = ET.tostring(root, 'utf-8')
    xml_doc = '<?xml version="1.0" encoding="UTF-8"?>' + xml_to_str.decode(
        'utf-8')
    logger.debug(xml_doc)

    return xml_doc


def parse_multi_ref_data(xml: str):
    root = ET.fromstring(xml)
    items = root.findall('RK7Reference/Items/Item')
    return [item.attrib for item in items]
