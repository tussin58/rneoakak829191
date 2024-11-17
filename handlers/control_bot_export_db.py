import os
import csv
from aiogram import types

from bot import dp
from modules import database


@dp.callback_query_handler(lambda call: call.data.startswith('export_db_'))
async def export_db(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    users = await database.get_all_constructor_users(bot_id)

    with open(f'data/{bot["name"]}-{bot_id}_users.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['telegram_id', 'registered_at'])

        for user in users:
            writer.writerow([user['user_id'], user['registered_at']])

    with open(f'data/{bot["name"]}-{bot_id}_users.csv', 'rb') as file:
        await call.message.answer_document(file, caption=f'База данных пользователей бота #{bot["name"]}', parse_mode='Markdown')

    os.remove(f'data/{bot["name"]}-{bot_id}_users.csv')