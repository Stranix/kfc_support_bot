from dataclasses import dataclass


@dataclass
class SyncStatus:
    server_name: str
    web_link: str
    status: str = 'ok'
    msg: str = 'In Progress'
