from aiogram import types

from bot import dp, user_states
from modules import database


@dp.callback_query_handler(lambda call: call.data.startswith('edit_domain_'))
async def edit_domain(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[call.from_user.id] = f'edit_domain_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('📝 _Введите новый домен для бота:_', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('edit_domain_'))
async def edit_domain(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    new_domain = message.text.strip()

    if not new_domain.startswith('https://'):
        await message.answer('🤖 _Домен должен начинаться с "https://"_', parse_mode='Markdown')
        return
    
    user_states[message.from_user.id] = None

    await database.update_bot(bot_id, 'domain', new_domain)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await message.answer('🤖 _Домен успешно изменен_', reply_markup=markup, parse_mode='Markdown')