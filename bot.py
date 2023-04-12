import handlers

from aiogram import executor
from loader import dp


if __name__ == '__main__':
    executor.start_polling(dp)
