import asyncio

import aioschedule
from aiogram import executor, types
from loader import dp, bot
import handlers
from services.check_mail import check_unread_mail


async def check_email():
    messages_for_send = check_unread_mail()
    if len(messages_for_send) > 0:
        await bot.send_message(chat_id='378630510', text='Поступило обращение на вашу группу')
        for msg in messages_for_send:
            await bot.send_message(chat_id='378630510', text=msg)


async def scheduler():
    aioschedule.every(1).minutes.do(check_email)
    while True:
        print('Шедулер')
        await aioschedule.run_pending()
        await asyncio.sleep(30)


async def on_startup(x):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp)
