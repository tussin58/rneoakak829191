from aiogram import types
from datetime import datetime, timedelta

from bot import dp
from modules import database


@dp.callback_query_handler(lambda call: call.data.startswith('bot_stats_'))
async def bot_stats(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    bot_users = await database.get_all_constructor_users(bot_id)

    all_users = len(bot_users)
    month_users = len([user for user in bot_users if datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S') > (datetime.utcnow() - timedelta(days=30))])
    week_users = len([user for user in bot_users if datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S') > (datetime.utcnow() - timedelta(days=7))])
    day_users = len([user for user in bot_users if datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S') > (datetime.utcnow() - timedelta(days=1))])
    hour_users = len([user for user in bot_users if datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S') > (datetime.utcnow() - timedelta(hours=1))])
    minute_users = len([user for user in bot_users if datetime.strptime(user['registered_at'], '%Y-%m-%d %H:%M:%S') > (datetime.utcnow() - timedelta(minutes=15))])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔄 Обновить', callback_data=f'bot_stats_{bot_id}'),
                types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    try:
        await call.message.edit_text(f'📊 *Статистика пользователей:*\n'
                                        f'└ 👥 Всего: `{all_users}`\n'
                                        f'└ 📅 Месяц: `{month_users}`\n'
                                        f'└ 📆 Неделя: `{week_users}`\n'
                                        f'└ 🗓 День: `{day_users}`\n'
                                        f'└ 🕐 Час: `{hour_users}`\n'
                                        f'└ ⏱ 15 мин: `{minute_users}`',
                                        reply_markup=markup, parse_mode='Markdown')
    except:
        pass