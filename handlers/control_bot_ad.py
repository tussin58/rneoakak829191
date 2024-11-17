import re
import os
from aiogram import types

from bot import dp, user_states
from modules import database, bots


user_ads = {}

@dp.callback_query_handler(lambda call: call.data.startswith('start_ad_'))
async def start_ad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    user_states[call.from_user.id] = f'ad_text_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('📨 *Отправьте сообщение для рассылки. Это может быть текст, фото, видео или GIF.*\n'
                                 '_(Поддерживается форматирование и переменная _`{telegram_id}`_)_',
                                 reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('ad_text_'), content_types=['text', 'photo', 'video', 'animation'])
async def ad_text(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[message.from_user.id] = f'ad_buttons_{bot_id}'
    user_ads[message.from_user.id] = {'bot_id': bot_id, 'text': message.html_text}

    if message.photo:
        user_ads[message.from_user.id]['photo'] = message.photo[-1].file_id
    elif message.video:
        user_ads[message.from_user.id]['video'] = message.video.file_id
    elif message.animation:
        user_ads[message.from_user.id]['animation'] = message.animation.file_id

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Пропустить кнопки', callback_data=f'skip_buttons_{bot_id}'))

    await message.answer('🔘 Контент для рассылки добавлен. Отправьте кнопки для рассылки в формате \[текст + URL] или \[текст + `webapp`]. Или нажмите кнопку, чтобы пропустить этот шаг.\n'
                         'P.S. _Webapp автоматически заменится на вебапп с выбранным доменом._',
                            reply_markup=markup, parse_mode='Markdown')
    

@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('ad_buttons_'))
@dp.callback_query_handler(lambda call: call.data.startswith('skip_buttons_'))
async def ad_buttons(event_data):
    if isinstance(event_data, types.Message):
        message = event_data
        bot_id = user_ads[message.from_user.id]['bot_id']

        bot_data = await database.get_bot(bot_id)
        if not bot_data:
            await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
            return

        markup = types.InlineKeyboardMarkup()

        for button in message.text.split('\n'):
            if not re.compile(r'\[.*\s\+\s(webapp|https://.*)\]').match(button.strip()):
                await message.answer(
                    '❌ _Неверный формат кнопок. Используйте [текст + URL] или [текст + webapp]_', 
                    parse_mode='Markdown'
                )
                return
        
            button = button.strip('[]')
            text, url = button.rsplit(' + ', 1)

            if url == 'webapp':
                url = bot_data['domain']

            markup.add(types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=url)))

        user_ads[message.from_user.id]['markup'] = markup
    else:
        call = event_data
        bot_id = int(call.data.split('_')[2])

        bot_data = await database.get_bot(bot_id)
        if not bot_data:
            await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
            return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('✅ Запустить рассылку', callback_data=f'confirm_ad_{bot_id}'),
                types.InlineKeyboardButton('❌ Отмена', callback_data=f'control_bot_{bot_id}'))

    if isinstance(event_data, types.Message):
        await message.answer('✅ Рассылка готова к отправке. Подтвердите запуск:', reply_markup=markup)
    else:
        await call.message.edit_text('✅ Рассылка готова к отправке. Подтвердите запуск:', reply_markup=markup)


@dp.callback_query_handler(lambda call: call.data.startswith('confirm_ad_'))
async def confirm_ad(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot_data = await database.get_bot(bot_id)
    if not bot_data:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    await call.message.edit_text('📤 *"Рассылка запущена. Это может занять некоторое время, вы будете уведомлены о результате...*', parse_mode='Markdown')

    users = await database.get_all_constructor_users(bot_id)

    success_count = 0
    error_count = 0

    ad_data = user_ads.get(call.from_user.id)
    if not ad_data:
        await call.message.edit_text('🤖 _Ошибка при отправке рассылки_', parse_mode='Markdown')
        return

    if ad_data.get('photo'):
        await dp.bot.download_file_by_id(ad_data['photo'], 'data/' + ad_data['photo'] + '.jpg')
    elif ad_data.get('video'):
        await dp.bot.download_file_by_id(ad_data['video'], 'data/' + ad_data['video'] + '.mp4')
    elif ad_data.get('animation'):
        await dp.bot.download_file_by_id(ad_data['animation'], 'data/' + ad_data['animation'] + '.gif')

    bot = bots.created_bots.get(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Произошла ошибка. Попробуйте перезапустить бота._', parse_mode='Markdown')
        return

    bot = bot['bot']

    for user in users:
        try:
            text = ad_data['text'].replace('{telegram_id}', str(user['user_id']))
            if ad_data.get('photo'):
                with open('data/' + ad_data['photo'] + '.jpg', 'rb') as file:
                    await bot.send_photo(user['user_id'], file, caption=text, reply_markup=ad_data.get('markup'), parse_mode='HTML')
            elif ad_data.get('video'):
                with open('data/' + ad_data['video'] + '.mp4', 'rb') as file:
                    await bot.send_video(user['user_id'], file, caption=text, reply_markup=ad_data.get('markup'), parse_mode='HTML')
            elif ad_data.get('animation'):
                with open('data/' + ad_data['animation'] + '.gif', 'rb') as file:
                    await bot.send_animation(user['user_id'], file, caption=text, reply_markup=ad_data.get('markup'), parse_mode='HTML')
            else:
                await bot.send_message(user['user_id'], text, reply_markup=ad_data.get('markup'), parse_mode='HTML')
            success_count += 1
        except:
            error_count += 1

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    if ad_data.get('photo'):
        os.remove('data/' + ad_data['photo'] + '.jpg')
    elif ad_data.get('video'):
        os.remove('data/' + ad_data['video'] + '.mp4')
    elif ad_data.get('animation'):
        os.remove('data/' + ad_data['animation'] + '.gif')

    if success_count + error_count == 0:
        await call.message.answer('❌ *В боте нет пользователей для отправки рассылки.*', reply_markup=markup, parse_mode='Markdown')
        return

    await call.message.answer('✅ *Рассылка успешно завершена!*\n\n'
                                 f'👤 *Всего пользователей:* {len(users)}\n'
                                f'📤 *Отправлено сообщений:* {success_count}\n'
                                f'❌ *Не удалось отправить:* {error_count}\n'
                                f'📈 *Процент успеха:* {success_count / (success_count + error_count) * 100:.2f}%',
                                reply_markup=markup, parse_mode='Markdown')