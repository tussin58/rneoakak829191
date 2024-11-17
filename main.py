import asyncio
from aiogram import executor, Bot, Dispatcher
from aiogram.types import BotCommand

import handlers
from bot import dp, bot
from modules import database, bots
from modules.database import create_db
from handlers.control_bot_interval_ad import start_interval_ad


async def on_startup(dp):
    await bot.set_my_commands([
        BotCommand('start', '🚀 Запустить бота')
    ])

    await create_db()

    all_bots = await database.get_all_bots()

    for constructor_bot in all_bots:
        if constructor_bot['status'] == 'running':
            task = asyncio.create_task(bots.start_bot(constructor_bot['id']))
            bots.created_bots[constructor_bot['id']] = {'task': task}
        else:
            bots.created_bots[constructor_bot['id']] = {'task': None,
                                                        'bot': Bot(token=constructor_bot['token']),
                                                        'dp': Dispatcher(Bot(token=constructor_bot['token']))}

        if constructor_bot['interval_ad_status'] == 1:
            bot_id = constructor_bot['id']
            while not bots.created_bots[bot_id].get('bot'):
                await asyncio.sleep(1)
            task =  asyncio.create_task(start_interval_ad(bot_id, bots.created_bots[bot_id]['bot'], constructor_bot['interval_ad_time'], constructor_bot['interval_ad_text'], constructor_bot['interval_ad_buttons']))
            bots.created_bots[bot_id]['interval_ad_task'] = task

    print('Bot started')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)