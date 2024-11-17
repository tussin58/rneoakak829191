from aiogram import types

import config
from bot import dp, user_states
from modules import database


async def main_menu_markup(user_id, page=0):
    markup = types.InlineKeyboardMarkup()

    bots = await database.get_user_bots(user_id)

    page_size = 7
    total_pages = (len(bots) + page_size - 1) // page_size

    if page < 0:
        page = 0
    elif page >= total_pages:
        page = total_pages - 1

    for bot in bots[page * page_size:page * page_size + page_size]:
        markup.add(types.InlineKeyboardButton('#' + bot['name'], callback_data=f'control_bot_{bot["id"]}'))

    markup.add(types.InlineKeyboardButton('➕ Добавить бота', callback_data='add_bot'))

    return markup


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = None

    if user_id not in config.ADMINS:
        return

    user = await database.get_user(user_id)
    if not user:
        await database.insert_user(user_id, message.from_user.username)
    elif user['username'] != message.from_user.username:
        await database.update_user(user_id, 'username', message.from_user.username)

    markup = await main_menu_markup(user_id)

    await message.answer('🤖 _Выберите нужного бота или создайте нового:_',
                         reply_markup=markup, parse_mode='Markdown')
    
    
@dp.callback_query_handler(lambda call: call.data == 'back_to_main_menu')
async def back_to_main_menu(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_states[user_id] = None

    markup = await main_menu_markup(user_id)
    
    await call.message.edit_text('🤖 _Выберите нужного бота или создайте нового:_',
                                reply_markup=markup, parse_mode='Markdown')