from aiogram import types

from bot import dp
from modules import database


async def control_bot_markup(bot_id) -> types.InlineKeyboardMarkup:
    bot = await database.get_bot(bot_id)
    if not bot:
        return None

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📝 Настройка ответов', callback_data=f'edit_answers_{bot_id}'),
                types.InlineKeyboardButton('📰 Запустить рассылку', callback_data=f'start_ad_{bot_id}'))
    if bot["status"] == 'stopped':
        markup.add(types.InlineKeyboardButton('🚀 Запустить', callback_data=f'run_bstatus_{bot_id}'),
                    types.InlineKeyboardButton('✋ Удалить бота', callback_data=f'delete_bot_{bot_id}'))
    else:
        markup.add(types.InlineKeyboardButton('⏹️ Остановить', callback_data=f'run_bstatus_{bot_id}'),
                    types.InlineKeyboardButton('✋ Удалить бота', callback_data=f'delete_bot_{bot_id}'))
    if bot["webapp_button"] == 0:
        markup.add(types.InlineKeyboardButton('❌ WebApp в углу', callback_data=f'webapp_bstatus_{bot_id}'),
                    types.InlineKeyboardButton('💬 Настроить текст WebApp', callback_data=f'edit_webapp_text_{bot_id}'))
    else:
        markup.add(types.InlineKeyboardButton('✅ WebApp в углу', callback_data=f'webapp_bstatus_{bot_id}'),
                    types.InlineKeyboardButton('💬 Настроить текст WebApp', callback_data=f'edit_webapp_text_{bot_id}'))
    markup.add(types.InlineKeyboardButton('🔄 Изменить домен', callback_data=f'edit_domain_{bot_id}'),
                types.InlineKeyboardButton('📊 Статистика', callback_data=f'bot_stats_{bot_id}'))
    markup.add(types.InlineKeyboardButton('📤 Экспорт базы данных', callback_data=f'export_db_{bot_id}'),
                types.InlineKeyboardButton('⏱️ Интервальная рассылка', callback_data=f'interval_ad_{bot_id}'))
    markup.add(types.InlineKeyboardButton('📨 Отправить сообщение по айди', callback_data=f'send_message_{bot_id}'))

    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main_menu'))\
    
    return markup


@dp.callback_query_handler(lambda call: call.data.startswith('control_bot_'))
async def control_bot(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    markup = await control_bot_markup(bot_id)

    text_buttons = await database.get_text_buttons(bot_id)
    text_buttons_text = ''
    for button in text_buttons:
        text_buttons_text += f'<blockquote>{button["name"]} - {button["text"]}</blockquote>\n'
    text_buttons_text = text_buttons_text if text_buttons_text else "<blockquote>❌ Не установлены</blockquote>"

    bot_buttons = '\n'.join([f'<blockquote>{button_name.strip()}</blockquote>' for button_name in bot["buttons"].split(',')]) if bot["buttons"] else "<blockquote>❌ Не установлены</blockquote>"

    await call.message.edit_text(f'🤖 <strong>Настройки бота</strong> #{bot["name"]}\n\n'
                                    f'<strong>🤖 Юзернейм:</strong> @{bot["username"]}\n'
                                    f'<strong>🖼 Медиа:</strong> {"✅ Установлено" if bot["media"] else "❌ <i>Не установлено</i>"}\n'
                                    f'<strong>🌐 Домен:</strong> {bot["domain"]}\n'
                                    f'<strong>💬 Текст кнопки WebApp:</strong> <code>{bot["webapp_button_text"]}</code>\n'
                                    f'<strong>🔽 Кнопки:</strong>\n{bot_buttons}\n\n'
                                    f'<strong>📝 Стартовый текст:</strong>\n<blockquote>{bot["start_text"] if bot["start_text"] else "❌ Не установлено"}</blockquote>\n\n'
                                    f'<strong>📝 Текстовые кнопки:</strong>\n{text_buttons_text}',

                                    reply_markup=markup, parse_mode='HTML')