from aiogram import types

from bot import dp, user_states
from modules import database, bots
from handlers.control_bot_menu import control_bot_markup


@dp.callback_query_handler(lambda call: call.data.startswith('webapp_bstatus_'))
async def webapp_bstatus(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if bot["webapp_button"] == 0:
        await bots.created_bots[bot_id]['bot'].set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                text=bot['webapp_button_text'],
                web_app=types.WebAppInfo(url=bot['domain'])
            )
        )

        await database.update_bot(bot_id, 'webapp_button', 1)
    else:
        await bots.created_bots[bot_id]['bot'].set_chat_menu_button(menu_button=types.MenuButtonDefault())

        await database.update_bot(bot_id, 'webapp_button', 0)

    markup = await control_bot_markup(bot_id)

    await call.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith('edit_webapp_text_'))
async def edit_webapp_text(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[3])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[call.from_user.id] = f'edit_webapp_text_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('📝 _Введите текст для кнопки WebApp (до 25 символов):_', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('edit_webapp_text_'))
async def edit_webapp_text(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[3])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if len(message.text) > 25:
        await message.answer('❌ _Текст кнопки не должен превышать 25 символов_', parse_mode='Markdown')
        return
    
    user_states[message.from_user.id] = None

    await database.update_bot(bot_id, 'webapp_button_text', message.text)

    if bot["webapp_button"] == 1:
        await bots.created_bots[bot_id]['bot'].set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(
                text=message.text,
                web_app=types.WebAppInfo(url=bot['domain'])
            )
        )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await message.answer('✅ _Текст кнопки успешно изменен_', reply_markup=markup, parse_mode='Markdown')