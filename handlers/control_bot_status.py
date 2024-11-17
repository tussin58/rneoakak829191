import asyncio
from aiogram import types

from bot import dp
from modules import database, bots
from handlers.control_bot_menu import control_bot_markup


@dp.callback_query_handler(lambda call: call.data.startswith('run_bstatus_'))
async def run_bstatus(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if bot["status"] == 'stopped':
        task = asyncio.create_task(bots.start_bot(bot_id))
        bots.created_bots[bot_id] = {'task': task}

        await database.update_bot(bot_id, 'status', 'running')
        markup = await control_bot_markup(bot_id)

        await call.message.edit_reply_markup(reply_markup=markup)
    else:
        await bots.stop_bot(bot_id)

        await database.update_bot(bot_id, 'status', 'stopped')
        markup = await control_bot_markup(bot_id)

        await call.message.edit_reply_markup(reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith('delete_bot_'))
async def delete_bot(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Да, удалить', callback_data=f'confirm_delete_{bot_id}'),
                types.InlineKeyboardButton('❌ Нет, отмена', callback_data=f'control_bot_{bot_id}'))
    
    await call.message.edit_text(f'❗️ Вы уверены, что хотите удалить бота #{bot["name"]}?\n'
                                    f'Это действие нельзя отменить.', reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith('confirm_delete_'))
async def confirm_delete(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if not bots.created_bots.get(bot_id):
        await call.answer('🤖 Ошибка при удалении бота', show_alert=True)
        return

    if bots.created_bots[bot_id]['task']:
        bots.created_bots[bot_id]['task'].cancel()
        try:
            await bots.created_bots[bot_id]['task']
        except asyncio.CancelledError:
            pass
    
    if bots.created_bots[bot_id].get('interval_ad_task'):
        bots.created_bots[bot_id]['interval_ad_task'].cancel()
        try:
            await bots.created_bots[bot_id]['interval_ad_task']
        except asyncio.CancelledError:
            pass

    await database.delete_bot(bot_id)
    del bots.created_bots[bot_id]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main_menu'))

    await call.message.edit_text('🤖 _Бот успешно удален_', reply_markup=markup, parse_mode='Markdown')