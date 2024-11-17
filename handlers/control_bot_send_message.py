import re
import os
from aiogram import types

from bot import dp, user_states
from modules import database, bots


messages = {}

@dp.callback_query_handler(lambda call: call.data.startswith('send_message_'))
async def send_message(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    user_states[call.from_user.id] = f'send_message_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('📨 *Отправьте сообщение которое нужно отправить. Это может быть текст, фото, видео или GIF.*\n'
                                 '_(Поддерживается форматирование)_',
                                 reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('send_message_'), content_types=['text', 'photo', 'video', 'animation'])
async def send_message(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[message.from_user.id] = f'pm_message_buttons_{bot_id}'

    messages[message.from_user.id] = {'bot_id': bot_id, 'text': message.html_text}
    
    if message.photo:
        messages[message.from_user.id]['photo'] = message.photo[-1].file_id
    elif message.video:
        messages[message.from_user.id]['video'] = message.video.file_id
    elif message.animation:
        messages[message.from_user.id]['animation'] = message.animation.file_id

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пропустить кнопки', callback_data=f'pm_skip_buttons_{bot_id}'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await message.answer('✅ Сообщение успешно сохранено! Отправьте кнопки для рассылки в формате \[текст + URL] или \[текст + `webapp`]. Или нажмите кнопку, чтобы пропустить этот шаг.\n'
                         'P.S. _Webapp автоматически заменится на вебапп с выбранным доменом._', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('pm_message_buttons_'))
@dp.callback_query_handler(lambda call: call.data.startswith('pm_skip_buttons_'))
async def pm_skip_buttons(event_data):
    if isinstance(event_data, types.Message):
        bot_id = int(user_states[event_data.from_user.id].split('_')[3])
    else:
        bot_id = int(event_data.data.split('_')[3])

    bot = await database.get_bot(bot_id)
    if not bot:
        await event_data.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    if isinstance(event_data, types.Message):
        for button in event_data.text.split('\n'):
            if not re.compile(r'\[.*\s\+\s(webapp|https://.*)\]').match(button.strip()):
                await event_data.answer('❌ Кнопки должны быть в формате \[текст + URL] или \[текст + `webapp`]', parse_mode='Markdown')
                return
            
        messages[event_data.from_user.id]['buttons'] = event_data.text
    else:
        messages[event_data.from_user.id]['buttons'] = None

    user_states[event_data.from_user.id] = 'pm_send_message_chat_id'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    if isinstance(event_data, types.Message):
        await event_data.answer('✅ Кнопки успешно сохранены! Теперь отправьте ID чата, куда нужно отправить сообщение:', reply_markup=markup)
    else:
        await event_data.message.edit_text('📨 *Введите ID чата, куда нужно отправить сообщение:*', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id] == 'pm_send_message_chat_id')
async def pm_send_message_chat_id(message: types.Message):
    bot_id = messages[message.from_user.id]['bot_id']

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    chat_id = message.text.strip()

    try:
        chat_id = int(chat_id)
    except ValueError:
        await message.answer('❌ _ID чата должен быть числом_', parse_mode='Markdown')
        return

    user_states[message.from_user.id] = None

    markup = types.InlineKeyboardMarkup()
    if messages[message.from_user.id].get('buttons'):
        for button in messages[message.from_user.id]['buttons'].split('\n'):
            if not button:
                continue

            button = button.strip('[]')
            text, url = button.rsplit(' + ', 1)

            if url == 'webapp':
                url = bot['domain']

            markup.add(types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=url)))

    try:
        if messages[message.from_user.id].get('photo'):
            await dp.bot.download_file_by_id(messages[message.from_user.id]['photo'], 'data/' + messages[message.from_user.id]['photo'] + '.jpg')

            with open('data/' + messages[message.from_user.id]['photo'] + '.jpg', 'rb') as photo:
                await bots.created_bots[bot_id]['bot'].send_photo(chat_id, photo, caption=messages[message.from_user.id]['text'], reply_markup=markup, parse_mode='HTML')
        elif messages[message.from_user.id].get('video'):
            await dp.bot.download_file_by_id(messages[message.from_user.id]['video'], 'data/' + messages[message.from_user.id]['video'] + '.mp4')

            with open('data/' + messages[message.from_user.id]['video'] + '.mp4', 'rb') as video:
                await bots.created_bots[bot_id]['bot'].send_video(chat_id, video, caption=messages[message.from_user.id]['text'], reply_markup=markup, parse_mode='HTML')
        elif messages[message.from_user.id].get('animation'):
            await dp.bot.download_file_by_id(messages[message.from_user.id]['animation'], 'data/' + messages[message.from_user.id]['animation'] + '.gif')

            with open('data/' + messages[message.from_user.id]['animation'] + '.gif', 'rb') as animation:
                await bots.created_bots[bot_id]['bot'].send_animation(chat_id, animation, caption=messages[message.from_user.id]['text'], reply_markup=markup, parse_mode='HTML')
        else:
            await bots.created_bots[bot_id]['bot'].send_message(chat_id, messages[message.from_user.id]['text'], reply_markup=markup, parse_mode='HTML')
    except:
        await message.answer('❌ _Не удалось отправить сообщение_', parse_mode='Markdown')
        return
    finally:
        try:
            if messages[message.from_user.id].get('photo'):
                os.remove('data/' + messages[message.from_user.id]['photo'] + '.jpg')
            elif messages[message.from_user.id].get('video'):
                os.remove('data/' + messages[message.from_user.id]['video'] + '.mp4')
            elif messages[message.from_user.id].get('animation'):
                os.remove('data/' + messages[message.from_user.id]['animation'] + '.gif')
        except FileNotFoundError:
            pass

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await message.answer('✅ *Сообщение успешно отправлено!*', reply_markup=markup, parse_mode='Markdown')