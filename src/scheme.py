from dataclasses import dataclass


@dataclass
class SyncStatus:
    web_link: str
    status: str = 'ok'
    msg: str = 'In Progress'
