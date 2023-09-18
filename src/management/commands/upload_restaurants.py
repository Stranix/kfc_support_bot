import logging

import requests.exceptions
from django.conf import settings
from django.core.management.base import BaseCommand

from src.referents.XmlInterface import XmlInterface
from src.referents.commands.GetRefData import get_ref_data
from src.referents.commands.GetRefData import parse_multi_ref_data

from src.models import FranchiseOwner
from src.models import Restaurant
from src.models import Server

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
        referents = Server.objects.get(
            franchise_owner__alias='yum',
            server_type__name='Referents',
        )
        r_keeper = XmlInterface(
            referents.ip,
            referents.web_server,
            settings.XML_LOGIN,
            settings.XML_PASSWORD,
        )
        try:
            r_keeper.check_settings_xml_interface()
            restaurants = get_restaurants_from_rkeeper(r_keeper)
            upload_restaurants(restaurants)
        except requests.exceptions.HTTPError as error:
            logger.exception(error)
        except requests.exceptions.ConnectionError:
            logger.error('Нет соединения с сервером справочников')


def get_restaurants_from_rkeeper(r_keeper: XmlInterface):
    prepare_command = {
        'cmd_param': {
            'OnlyActive': '1',
            'WithMacroProp': '1',
        }
    }
    xml_command = get_ref_data('Restaurants', prepare_command)
    r_keeper_answer = r_keeper.send_data(xml_command)
    restaurants = parse_multi_ref_data(r_keeper_answer)
    return restaurants


def upload_restaurants(restaurants):
    logger.info('Запись ресторанов в базу')
    for restaurant in restaurants:
        logger.debug('Обработка ресторана: %s', restaurant['Name'])
        if restaurant['Name'] == 'Центральный Офис':
            continue
        owner = restaurant['Owner'].replace('&quot;', '"')
        franchise = get_franchise_by_owner(owner)
        restaurant_db, _ = Restaurant.objects.update_or_create(
            id=int(restaurant['Ident']),
            defaults={
                'name': restaurant['Name'],
                'code': int(restaurant['Code']),
                'legal_entity': owner,
                'address': restaurant['Address'],
                'phone': restaurant['gentelephone_number'],
                'server_ip': restaurant['genIP_REP_SRV'],
                'franchise': franchise,
                'is_sync': False if franchise.alias == 'fz' else True,
            }
        )
        logger.debug('Добавлен')
    logger.info('Запись ресторанов в базу завершена')


def get_franchise_by_owner(owner: str):
    franchise_alias = 'fz'
    if owner.lower().find('ям') != -1:
        franchise_alias = 'yum'
    if owner.lower().find('интернэшнл') != -1:
        franchise_alias = 'irb'
    return FranchiseOwner.objects.get(alias=franchise_alias)
