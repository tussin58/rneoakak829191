from aiogram import types

from bot import dp, bot, user_states
from modules import database


@dp.callback_query_handler(lambda call: call.data == 'send_message')
async def send_message(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_states[user_id] = 'send_message'

    await call.message.edit_text('📝 *Рассылка*\n'
                                 '🔽 _Введите текст сообщения:_',
                                 parse_mode='Markdown')
    
    
@dp.message_handler(lambda message: user_states.get(message.from_user.id) == 'send_message', content_types=['text', 'photo'])
async def send_message_handler(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = None

    users = await database.get_all_users()

    await message.answer('📤 *"Рассылка запущена. Это может занять некоторое время, вы будете уведомлены о результате...*', parse_mode='Markdown')

    success_count = 0
    error_count = 0

    if message.photo:
        for user in users:
            try:
                await bot.send_photo(user['user_id'], message.photo[-1].file_id, caption=message.caption)
                success_count += 1
            except:
                error_count += 1
    else:
        for user in users:
            try:
                await bot.send_message(user['user_id'], message.text)
                success_count += 1
            except:
                error_count += 1

    await message.answer('✅ *Рассылка успешно завершена!*\n\n'
                            f'📤 *Отправлено сообщений:* {success_count}\n'
                            f'❌ *Не удалось отправить:* {error_count}', parse_mode='Markdown')