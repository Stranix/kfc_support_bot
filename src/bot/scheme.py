from datetime import datetime
from datetime import timedelta

from typing import Union

from dataclasses import dataclass

from src.models import Task


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
    shift_start_at: datetime
    shift_end_at: datetime
    total_breaks_time: timedelta
    tasks_closed: int
    avg_tasks_rating: float = 0.0


@dataclass
class EngineersOnShift:
    count: int
    engineers: list[EngineerShiftInfo]
    middle_engineers: list[EngineerShiftInfo]


@dataclass
class TasksOnShift:
    count: int
    closed: int
    avg_processing_time: timedelta
    tasks: Union[list[Task], list]
    avg_rating: float = 0.0
