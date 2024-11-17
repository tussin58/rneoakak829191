import random
import string
from aiogram import Bot, Dispatcher, types

from bot import dp, user_states
from modules import database


async def generate_random_name():
    letters = ''.join(random.choices(string.ascii_lowercase, k=6))
    digits = ''.join(random.choices(string.digits, k=4))
    return letters + digits


new_bots = {}

@dp.callback_query_handler(lambda call: call.data == 'add_bot')
async def add_bot(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_states[user_id] = 'add_bot_domain'

    new_bots[user_id] = {}

    await call.message.edit_text('🤖 _Введите домен вашего бота:_', parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'add_bot_domain')
async def add_bot_domain(message: types.Message):
    user_id = message.from_user.id

    if not message.text.startswith('https://'):
        await message.answer('🤖 _Домен должен начинаться с_ `https://`', parse_mode='Markdown')
        return

    user_states[user_id] = 'add_bot_token'

    new_bots[user_id]['domain'] = message.text

    await message.answer('🤖 _Введите токен вашего бота:_', parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'add_bot_token')
async def add_bot_token(message: types.Message):
    user_id = message.from_user.id

    try:
        new_bot = Bot(token=message.text)
        username = (await new_bot.get_me()).username
    except Exception as e:
        await message.answer(f'🤖 _Неверный токен._', parse_mode='Markdown')
        return
    finally:
        if 'new_bot' in locals():
            session = await new_bot.get_session()
            await session.close()

    user_states[user_id] = None

    new_bots[user_id]['token'] = message.text
    new_bots[user_id]['username'] = username
    new_bots[user_id]['name'] = await generate_random_name()

    await database.insert_bot(user_id, new_bots[user_id]['name'], new_bots[user_id]['username'], new_bots[user_id]['domain'], new_bots[user_id]['token'])

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main_menu'))

    await message.answer('🤖 _Бот успешно добавлен!_', reply_markup=markup, parse_mode='Markdown')