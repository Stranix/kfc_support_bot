import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from src.referents.XmlInterface import XmlInterface
from src.referents.commands.GetRefData import get_ref_data
from src.referents.commands.GetRefData import parse_multi_ref_data

from src.models import Server, FranchiseOwner
from src.models import ServerType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open('config/logging_config.json', 'r', encoding='utf-8') as file:
            logging.config.dictConfig(json.load(file))

        yum_tr_groups_name = ['REP_CENTER', 'FZ_REP_TRANSIT']
        irb_tr_groups_name = ['RS_REP_TRANSIT']

        referents_yum = Server.objects.get(
            server_type__name='Referents',
            franchise_owner__alias='yum',
        )
        referents_irb = Server.objects.get(
            server_type__name='Referents',
            franchise_owner__alias='irb',
        )

        r_keeper_yum = XmlInterface(
            referents_yum.ip,
            referents_yum.web_server,
            settings.XML_LOGIN,
            settings.XML_PASSWORD,
        )
        r_keeper_irb = XmlInterface(
            referents_irb.ip,
            referents_irb.web_server,
            settings.XML_LOGIN,
            settings.XML_PASSWORD,
        )
        tr_servers = []
        for yum_group_name in yum_tr_groups_name:
            yum_tr_servers = get_rk_tr_info_by_name(
                r_keeper_yum,
                yum_group_name,
            )
            tr_servers.extend(yum_tr_servers)
        for irb_group_name in irb_tr_groups_name:
            irb_tr_servers = get_rk_tr_info_by_name(
                r_keeper_irb,
                irb_group_name,
            )
            tr_servers.extend(irb_tr_servers)
        upload_transits(tr_servers)


def upload_transits(servers: list):
    tr_server_type = ServerType.objects.get(name='Transit')
    tr_owner_yum = FranchiseOwner.objects.get(alias='yum')
    tr_owner_irb = FranchiseOwner.objects.get(alias='irb')
    tr_owner_fz = FranchiseOwner.objects.get(alias='fz')
    tr_ip = '192.168.221.24'
    tr_owner = tr_owner_yum
    for server in servers:
        if server['Name'].find('FZ_REP') != -1:
            tr_ip = '95.181.206.172'
            tr_owner = tr_owner_fz
        if server['Name'].find('RS_REP') != -1:
            tr_ip = '10.200.103.223'
            tr_owner = tr_owner_irb

        Server.objects.update_or_create(
            id=server['Ident'],
            defaults={
                'name': server['Name'],
                'ip': tr_ip,
                'web_server': server['HTTPServPort'],
                'server_type': tr_server_type,
                'franchise_owner': tr_owner,
                'is_sync': True,
            }
        )


def get_rk_tr_info_by_name(r_keeper: XmlInterface, name: str) -> list:
    prepare_command = {
        'cmd_param': {
            'OnlyActive': '1',
            'PropMask': r'{Name, HTTPServPort}',
        },
        'propfilters': {
            'Name': 'Name',
            'Substring': name
        }

    }
    xml_command = get_ref_data('ReportingServers', prepare_command)
    r_keeper_answer = r_keeper.send_data(xml_command)
    return parse_multi_ref_data(r_keeper_answer)
