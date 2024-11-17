import re
import os
from aiogram import types

from bot import dp, user_states
from modules import database


@dp.callback_query_handler(lambda call: call.data.startswith('edit_answers_'))
async def edit_answers(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('📝 Изменить стартовый текст', callback_data=f'set_start_text_{bot_id}'))
    markup.add(types.InlineKeyboardButton('🖼 Добавить медиа', callback_data=f'control_media_{bot_id}'),
                types.InlineKeyboardButton('🔘 Управление кнопками', callback_data=f'control_buttons_{bot_id}'))
    markup.add(types.InlineKeyboardButton('💠 Текстовые кнопки', callback_data=f'text_buttons_{bot_id}'))
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('💁‍♂️ _Выберите действие:_', reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('set_start_text_'))
async def set_start_text(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[3])

    user_states[call.from_user.id] = f'set_start_text_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Отмена', callback_data=f'control_bot_{bot_id}'))

    await call.message.edit_text('''📝 Введите новый стартовый текст для вашего бота:
_(Поддерживается форматирование)_

Вы можете использовать следующие переменные:
`{first_name}` - имя пользователя
`{last_name}` - фамилия пользователя
`{username}` - имя пользователя без @
`{telegram_id}` - ID пользователя в Telegram

Если какое-то поле отсутствует, оно будет заменено на пустую строку.''', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('set_start_text_'))
async def set_start_text(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[3])

    user_states[message.from_user.id] = None

    await database.update_bot(bot_id, 'start_text', message.html_text)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'control_bot_{bot_id}'))

    await message.answer('✅ _Стартовый текст успешно обновлен_', reply_markup=markup, parse_mode='Markdown')
    

@dp.callback_query_handler(lambda call: call.data.startswith('control_media_'))
async def control_media(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[call.from_user.id] = f'add_media_{bot_id}'

    markup = types.InlineKeyboardMarkup()

    if bot['media']:
        markup.add(types.InlineKeyboardButton('🗑️ Удалить текущее медиа', callback_data=f'delete_media_{bot_id}'))

    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await call.message.edit_text('🔽 _Отправьте медиа или выберите опцию:_', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('add_media_'), content_types=['photo'])
async def add_media(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    user_states[message.from_user.id] = None

    bot = await database.get_bot(bot_id)
    if not bot:
        await message.answer('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    await dp.bot.download_file_by_id(message.photo[-1].file_id, 'data/media/' + str(bot_id) + '.jpg')
    
    await database.update_bot(bot_id, 'media', 'data/media/' + str(bot['id']) + '.jpg')

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await message.answer('✅ _Медиафайлы успешно сохранены!_', reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('delete_media_'))
async def delete_media(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    try:
        os.remove(bot['media'])
    except FileNotFoundError:
        pass

    await database.update_bot(bot_id, 'media', None)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await call.message.edit_text('✅ _Медиафайлы удалены. Отправьте новые медиа или вернитесь назад:_', reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('control_buttons_'))
async def control_buttons(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return

    user_states[call.from_user.id] = f'control_buttons_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await call.message.edit_text('''🔘 _Введите кнопки в формате:_
_[текст + url] или [текст +_ `webapp`_]
Каждая кнопка с новой строки. Максимум 5x5 кнопок.
P.S. Webapp автоматически заменится на вебапп с выбранным доменом_''', reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('control_buttons_'))
async def control_buttons(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    for line in message.text.split('\n'):
        if not re.compile(r'\[.*\s\+\s(webapp|https://.*)\]').match(line.strip()):
            await message.answer(
                '❌ _Неверный формат кнопки. Используйте [текст + URL] или [текст + webapp]_', 
                parse_mode='Markdown'
            )
            return

    user_states[message.from_user.id] = None

    await database.update_bot(bot_id, 'buttons', message.text)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await message.answer('✅ _Кнопки успешно обновлены_', reply_markup=markup, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('text_buttons_'))
async def text_buttons(call: types.CallbackQuery):
    bot_id = int(call.data.split('_')[2])

    bot = await database.get_bot(bot_id)
    if not bot:
        await call.message.edit_text('🤖 _Бот не найден_', parse_mode='Markdown')
        return
    
    user_states[call.from_user.id] = f'text_buttons_{bot_id}'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await call.message.edit_text('🔘 _Введите текстовые кнопки в формате:_\n_[Название + Текст кнопки] каждая кнопка с новой строки_\n\n'
                                 '⚠️ _Чтобы удалить текущие кнопки отправьте_ `Удалить все кнопки` _(кликабельно)_',
                                   reply_markup=markup, parse_mode='Markdown')


@dp.message_handler(lambda message: user_states.get(message.from_user.id) and user_states[message.from_user.id].startswith('text_buttons_'))
async def text_buttons(message: types.Message):
    bot_id = int(user_states[message.from_user.id].split('_')[2])

    await database.delete_text_buttons(bot_id)

    if message.text == 'Удалить все кнопки':
        user_states[message.from_user.id] = None

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

        await message.answer('✅ _Текстовые кнопки удалены_', reply_markup=markup, parse_mode='Markdown')
        return

    for line in message.html_text.split('\n'):
        if not re.compile(r'\[.*\s\+\s.*\]').match(line.strip()):
            await message.answer(
                '❌ _Неверный формат кнопки. Используйте [название + текст кнопки]_', 
                parse_mode='Markdown'
            )

            await database.delete_text_buttons(bot_id)
            return
        
        name, text = line.strip('[]').split(' + ')

        await database.insert_text_button(bot_id, name, text)

    user_states[message.from_user.id] = None

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data=f'edit_answers_{bot_id}'))

    await message.answer('✅ _Текстовые кнопки успешно обновлены_', reply_markup=markup, parse_mode='Markdown')


