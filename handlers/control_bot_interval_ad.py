import re
import asyncio
from aiogram import types

from bot import dp, user_states
from modules import database, bots


@dp.callback_query_handler(lambda call: call.data.startswith('interval_ad_'))
async def interval_ad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⏱️ Установить интервал', callback_data=f'set_intad_{bot_id}'),
                types.InlineKeyboardButton('📝 Настроить сообщение', callback_data=f'msg_intad_{bot_id}'))
    if bot['interval_ad_status'] == 1:
        markup.add(types.InlineKeyboardButton('❌ Выключить', callback_data=f'status_intad_{bot_id}'))
    else:
        markup.add(types.InlineKeyboardButton('✅ Включить', callback_data=f'status_intad_{bot_id}'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    interval_hours = bot['interval_ad_time'] // 60
    interval_minutes = bot['interval_ad_time'] % 60

    await call.message.edit_text(f'''⚙️ *Текущие настройки интервальной рассылки:*
⏱ *Интервал:* `{interval_hours} ч. {interval_minutes} мин.`
📝 *Текст:* \n`{bot['interval_ad_text'] if bot['interval_ad_text'] else '❌ Не установлено'}`
🔘 *Кнопки:* \n`{bot['interval_ad_buttons'] if bot['interval_ad_buttons'] else '❌ Кнопки не установлены'}`''',\
                                reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('set_intad_'))
async def set_intad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    user_states[call.from_user.id] = f'set_intad_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'interval_ad_{bot_id}'))

    await call.message.edit_text('⏱ *Введите интервал рассылки в минутах (от 60 до 2880):*', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('set_intad_'))
async def set_intad(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    interval = int(message.text.strip())
    if interval < 60 or interval > 2880:
        await message.answer('⚠️ _Интервал должен быть от 60 до 2880 минут_', parse_mode='Markdown')
        return

    user_states[message.from_user.id] = None

    await database.update_bot(bot_id, 'interval_ad_time', interval)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'interval_ad_{bot_id}'))

    await message.answer('✅ _Интервал успешно установлен_', reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('msg_intad_'))
async def msg_intad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    user_states[call.from_user.id] = f'msg_intad_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'interval_ad_{bot_id}'))

    await call.message.edit_text('📝 *Отправьте сообщение для интервальной рассылки.*\n'
                                 'Это может быть текст, фото, видео или GIF.\n'
                                '_(Поддерживается форматирование)_',
                                reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('msg_intad_'), content_types=['text', 'photo', 'video', 'animation'])
async def msg_intad(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[message.from_user.id] = f'buttons_intad_{bot_id}'

    if message.photo:
        await dp.bot.download_file_by_id(message.photo[-1].file_id, 'data/media/ad_' + str(bot_id) + '.jpg')
        await database.update_bot(bot_id, 'interval_ad_media_type', 'photo')
    elif message.video:
        await dp.bot.download_file_by_id(message.video.file_id, 'data/media/ad_' + str(bot_id) + '.mp4')
        await database.update_bot(bot_id, 'interval_ad_media_type', 'video')
    elif message.animation:
        await dp.bot.download_file_by_id(message.animation.file_id, 'data/media/ad_' + str(bot_id) + '.gif')
        await database.update_bot(bot_id, 'interval_ad_media_type', 'animation')
    else:
        await database.update_bot(bot_id, 'interval_ad_media_type', None)

    await database.update_bot(bot_id, 'interval_ad_text', message.html_text)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пропустить кнопки', callback_data=f'ad_skip_buttons_{bot_id}'))

    await message.answer('🔘 Контент для интервальной рассылки добавлен. Отправьте кнопки для рассылки в формате \[текст + URL] или \[текст + `webapp`]. Или нажмите кнопку, чтобы пропустить этот шаг.\n'
                         'P.S. _Webapp автоматически заменится на вебапп с выбранным доменом._',
                         reply_markup=markup, parse_mode='Markdown')
    

@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('buttons_intad_'))
@dp.callback_query_handler(lambda call: call.data.startswith('ad_skip_buttons_'))
async def buttons_intad(event_data):
    if isinstance(event_data, types.Message):
        message = event_data
        bot_id = int(user_states[message.from_user.id].split('_')[2])
    else:
        call = event_data
        bot_id = int(call.data.split('_')[3])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if isinstance(event_data, types.Message):
        for button in message.text.split('\n'):
            if not re.compile(r'\[.*\s\+\s(webapp|https://.*)\]').match(button.strip()):
                await message.answer('❌ Каждая кнопка должна быть в формате: \[текст + URL] или \[текст + `webapp`]', parse_mode='Markdown')
                return

        if len(message.text.split('\n')) >= 25:
            await message.answer('❌ _Максимум 25 кнопок_', parse_mode='Markdown')
            return

        await database.update_bot(bot_id, 'interval_ad_buttons', message.text)
    else:
        await database.update_bot(bot_id, 'interval_ad_buttons', None)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'interval_ad_{bot_id}'))

    if isinstance(event_data, types.Message):
        await message.answer('✅ _Кнопки для интервальной рассылки установлены!_', reply_markup=markup, parse_mode='Markdown')
    else:
        await call.message.edit_text('✅ _Кнопки для интервальной рассылки пропущены_', reply_markup=markup, parse_mode='Markdown')


async def start_interval_ad(bot_id, bot, interval, message, buttons):
    while True:
        markup = types.InlineKeyboardMarkup()
        
        await asyncio.sleep(interval * 60)

        users = await database.get_all_constructor_users(bot_id)

        bot_data = await database.get_bot(bot_id)

        if buttons:
            for button in buttons.split('\n'):
                button = button.strip('[]')
                text, url = button.rsplit(' + ', 1)

                if url == 'webapp':
                    url = bot_data['domain']

                markup.add(types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=url)))
        
        for user in users:
            try:
                if bot_data['interval_ad_media_type'] == 'photo':
                    with open('data/media/ad_' + str(bot_id) + '.jpg', 'rb') as photo:
                        await bot.send_photo(user['user_id'], photo, caption=message, reply_markup=markup, parse_mode='HTML')
                elif bot_data['interval_ad_media_type'] == 'video':
                    with open('data/media/ad_' + str(bot_id) + '.mp4', 'rb') as video:
                        await bot.send_video(user['user_id'], video, caption=message, reply_markup=markup, parse_mode='HTML')
                elif bot_data['interval_ad_media_type'] == 'animation':
                    with open('data/media/ad_' + str(bot_id) + '.gif', 'rb') as animation:
                        await bot.send_animation(user['user_id'], animation, caption=message, reply_markup=markup, parse_mode='HTML')
                else:
                    await bot.send_message(user['user_id'], message, reply_markup=markup, parse_mode='HTML')
            except:
                pass


@dp.callback_query_handler(lambda call: call.data.startswith('status_intad_'))
async def status_intad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    if not bot['interval_ad_text'] and not bot['interval_ad_media_type']:
        await call.answer('❌ Не установлено сообщение для рассылки', show_alert=True)
        return

    if bot['interval_ad_status'] == 1:
        if bots.created_bots[bot_id].get('interval_ad_task'):
            bots.created_bots[bot_id]['interval_ad_task'].cancel()
            try:
                await bots.created_bots[bot_id]['interval_ad_task']
            except asyncio.CancelledError:
                pass

            bots.created_bots[bot_id]['interval_ad_task'] = None

        await database.update_bot(bot_id, 'interval_ad_status', 0)
    else:
        if not bots.created_bots[bot_id].get('interval_ad_task'):
            bots.created_bots[bot_id]['interval_ad_task'] = asyncio.create_task(start_interval_ad(bot_id, bots.created_bots[bot_id]['bot'], bot['interval_ad_time'], bot['interval_ad_text'], bot['interval_ad_buttons']))
        else:
            await call.answer('❌ Ошибка при запуске рассылки', show_alert=True)
            return
        
        await database.update_bot(bot_id, 'interval_ad_status', 1)

    markup = types.InlineKeyboardMarkup()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⏱️ Установить интервал', callback_data=f'set_intad_{bot_id}'),
                types.InlineKeyboardButton('📝 Настроить сообщение', callback_data=f'msg_intad_{bot_id}'))
    if bot['interval_ad_status'] == 0:
        markup.add(types.InlineKeyboardButton('❌ Выключить', callback_data=f'status_intad_{bot_id}'))
    else:
        markup.add(types.InlineKeyboardButton('✅ Включить', callback_data=f'status_intad_{bot_id}'))

    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_reply_markup(reply_markup=markup)