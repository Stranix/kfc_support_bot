import logging

from aiogram import executor
from loader import dp
import handlers

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    executor.start_polling(dp)
