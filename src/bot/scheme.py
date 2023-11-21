from datetime import datetime

from dataclasses import dataclass

from src.models import GSDTask


@dataclass
class SyncStatus:
    server_name: str
    web_link: str
    status: str = 'ok'
    msg: str = 'In Progress'


@dataclass
class TelegramUser:
    id: int
    nickname: str


@dataclass
class EngineerShiftInfo:
    name: str
    group: str
    shift_start_at: datetime
    shift_end_at: datetime
    total_breaks_time: str
    tasks_closed: int
    avg_tasks_rating: float = 0.0


@dataclass
class EngineersOnShift:
    count: int
    engineers: list[EngineerShiftInfo]
    middle_engineers: list[EngineerShiftInfo]
    dispatchers: list[EngineerShiftInfo]
    dispatchers_count: int


@dataclass
class TasksOnShift:
    count: int
    closed: int
    avg_processing_time: str
    tasks: list[GSDTask]
    avg_rating: float = 0.0
