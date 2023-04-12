import logging
import urllib3
import env_config as config

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
FORMAT = '%(asctime)s %(levelname)s : %(message)s'

logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='bot.log'
)

logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
