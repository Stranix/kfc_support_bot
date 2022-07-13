import logging

import urllib3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import env_config as config


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p', filename='bot.log')
logger = logging.getLogger(__name__)
logger.info(config.BOT_TOKEN)
bot = Bot(token='437843962:AAEuSAFw6cwDn8B75yS6n1v7kXWeXJiU7D4', parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
