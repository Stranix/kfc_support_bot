import logging

from aiogram import types
from aiogram.dispatcher import filters

from loader import dp
from services.synchronization import found_rest_in_ref, get_rest_info_by_code, sync_rep


@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=[r'(\d{2,4}\s?)+']))
async def send_welcome(message: types.Message, regexp_command):
    restaurants = regexp_command.group()
    logging.info(f'Запуск от: {message.from_user.full_name}')
    logging.info(f'Получил ресторан(ы): {restaurants}')
    codes = str(restaurants).split(' ')
    sync_results = list()
    for code in codes:
        logging.info(f'Получаю информацию по ресторану с кодом {code}')
        rest_info = get_rest_info_by_code(code)
        if rest_info['founded']:
            logging.info(f'Информация по ресторану получена.')
            logging.info('Запускаю синхронизацию')
            start_sync = sync_rep(rest_info['web_link'])
            rest_info['sync_status'] = start_sync['status']
            sync_results.append(rest_info)
        else:
            logging.error(f'Информация по ресторану не получена. {code} Рест не найден')
            found_rest = found_rest_in_ref(int(code))
            logging.info(found_rest)
            
            rest_info['code'] = code
            sync_results.append(rest_info)
    not_found = ''
    sync_start = ''
    sync_error = ''
    for rest in sync_results:
        if not rest['founded']:
            not_found += rest['code'] + ' '
            continue
        if rest['sync_status'] == 'In Progress':
            sync_start += f'{rest["rest_name"]} : {rest["web_link"]}\n'
        else:
            sync_error += f'\n{rest["rest_name"]} : {rest["web_link"]}\nОшибка: {rest["sync_status"]}\n'

    message_for_send = ''
    if not_found != '':
        message_for_send += 'Не нашел информацию по ресторану(ам): ' + not_found + '\n'
    if sync_start != '':
        message_for_send += 'Синхронизация запущена для:\n' + sync_start
    if sync_error != '':
        message_for_send += 'Ошибка старта синхронизации:\n' + sync_error

    await message.reply(message_for_send)


@dp.message_handler(commands='sync_rest')
async def create_deeplink(message: types.Message):
    text = (
        f'Пример команды: <code>/sync_rest 5028 12 1840</code>'
    )
    await message.reply(text)
