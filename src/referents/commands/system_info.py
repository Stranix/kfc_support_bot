import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger('xml_interface')


def get_system_info_xml() -> str:
    """Генерация XML файла для команды GetSystemInfo"""

    root = ET.Element("RK7Query")
    rk7cmd = ET.SubElement(root, 'RK7CMD')
    rk7cmd.set('CMD', 'GetSystemInfo')
    xml_to_str = ET.tostring(root, 'utf-8')
    xml_doc = '<?xml version="1.0" encoding="UTF-8"?>' + \
              xml_to_str.decode('utf-8')
    logger.debug(xml_doc)
    return xml_doc


def parse_get_system_info(xml: str):
    """Парсим ответ от команды"""

    root = ET.fromstring(xml)
    ref_version = root.attrib['ServerVersion']
    net_name = root.attrib['NetName']

    return net_name, ref_version
