import asyncio
from aiogram import Bot, Dispatcher, types

from modules import database

created_bots = {}

async def start_bot(bot_id):
    bot_info = await database.get_bot(bot_id)

    if not bot_info:
        return

    bot = Bot(token=bot_info['token'])
    dp = Dispatcher(bot)

    created_bots[bot_id]['bot'] = bot
    created_bots[bot_id]['dp'] = dp

    @dp.message_handler(commands=['start'])
    @dp.callback_query_handler(lambda call: call.data == 'back')
    async def start(event_data):
        user_id = event_data.from_user.id
        bot_data = await database.get_bot(bot_id)

        user = await database.get_constructor_user(user_id, bot_id)

        if not user:
            await database.insert_constructor_user(user_id, bot_id)
            user = await database.get_constructor_user(user_id, bot_id)

        markup = types.InlineKeyboardMarkup()

        if bot_data['buttons']:
            for button in bot_data['buttons'].split('\n'):
                button = button.strip('[]')
                text, url = button.rsplit(' + ', 1)

                if url == 'webapp':
                    markup.add(types.InlineKeyboardButton(text, web_app=types.WebAppInfo(url=bot_data['domain'])))
                else:
                    markup.add(types.InlineKeyboardButton(text, url=url))

        text_buttons = await database.get_text_buttons(bot_id)
        for button in text_buttons:
            markup.add(types.InlineKeyboardButton(button['name'], callback_data=f'text_button_{button["id"]}'))

        start_text = bot_data['start_text'] if bot_data['start_text'] else ''

        if start_text:
            start_text = start_text.replace('{first_name}', event_data.from_user.first_name or '')
            start_text = start_text.replace('{last_name}', event_data.from_user.last_name or '')
            start_text = start_text.replace('{username}', event_data.from_user.username or '')
            start_text = start_text.replace('{telegram_id}', str(event_data.from_user.id) or '')

        if isinstance(event_data, types.Message):
            message = event_data
        else:
            message = event_data.message

        if bot_data['media']:
            with open(f'{bot_data["media"]}', 'rb') as photo:
                await message.answer_photo(photo, caption=start_text, reply_markup=markup, parse_mode='HTML')
        elif start_text:
            await message.answer(start_text, reply_markup=markup, parse_mode='HTML')

        if isinstance(event_data, types.CallbackQuery):
            await event_data.message.delete()

    @dp.callback_query_handler(lambda call: call.data.startswith('text_button_'))
    async def text_button(call: types.CallbackQuery):
        button_id = int(call.data.split('_')[2])

        button = await database.get_text_button(button_id)
        if not button:
            return

        user_id = call.from_user.id
        bot_id = button['bot_id']

        user = await database.get_constructor_user(user_id, bot_id)
        if not user:
            return
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🔙 Back', callback_data=f'back'))

        await call.message.answer(button['text'], reply_markup=markup, parse_mode='HTML')
        await call.message.delete()


    @dp.message_handler(content_types=types.ContentTypes.ANY)
    async def register_user(message: types.Message):
        user_id = message.from_user.id

        user = await database.get_constructor_user(user_id, bot_id)
        if not user:
            await database.insert_constructor_user(user_id, bot_id)
            user = await database.get_constructor_user(user_id, bot_id)


    try:
        await dp.start_polling()
    except:
        pass

async def stop_bot(bot_id):
    if bot_id in created_bots:
        task = created_bots[bot_id]['task']
        dp = created_bots[bot_id]['dp']
        bot = created_bots[bot_id]['bot']
        
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        dp.stop_polling()
        await dp.wait_closed()
        
        session = await bot.get_session()
        await session.close()
        
        created_bots[bot_id]['task'] = None