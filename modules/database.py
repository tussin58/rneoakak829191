import aiosqlite


async def create_db():
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                username TEXT DEFAULT NULL,
                start_text TEXT DEFAULT NULL,
                media TEXT DEFAULT NULL,
                webapp_button INTEGER DEFAULT 0,
                webapp_button_text TEXT DEFAULT 'App',
                buttons TEXT DEFAULT NULL,
                domain TEXT NOT NULL,
                status TEXT DEFAULT 'stopped',
                interval_ad_time INTEGER DEFAULT 60,
                interval_ad_text TEXT DEFAULT NULL,
                interval_ad_media_type TEXT DEFAULT NULL,
                interval_ad_buttons TEXT DEFAULT NULL,
                interval_ad_status INTEGER DEFAULT 0,
                token TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                         
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS constructor_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (bot_id) REFERENCES bots (id),
                UNIQUE (user_id, bot_id)
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS text_buttons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                text TEXT NOT NULL,
                
                FOREIGN KEY (bot_id) REFERENCES bots (id)
            )
        ''')
        await db.commit()


async def insert_user(user_id, username):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''INSERT INTO users (user_id, username) VALUES (?, ?)''', (user_id, username))
        await db.commit()


async def insert_constructor_user(user_id, bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''INSERT INTO constructor_bots (user_id, bot_id) VALUES (?, ?)''', (user_id, bot_id))
        await db.commit()


async def insert_bot(user_id, name, username, domain, token):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''INSERT INTO bots (user_id, name, username, domain, token) VALUES (?, ?, ?, ?, ?)''', (user_id, name, username, domain, token))
        await db.commit()


async def insert_text_button(bot_id, name, text):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''INSERT INTO text_buttons (bot_id, name, text) VALUES (?, ?, ?)''', (bot_id, name, text))
        await db.commit()


async def update_user(user_id, column, value):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute(f'''UPDATE users SET {column} = ? WHERE user_id = ?''', (value, user_id))
        await db.commit()


async def update_bot(bot_id, column, value):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute(f'''UPDATE bots SET {column} = ? WHERE id = ?''', (value, bot_id))
        await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,)) as cursor:
            return await cursor.fetchone()
        
    
async def get_constructor_user(user_id, bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM constructor_bots WHERE user_id = ? AND bot_id = ?''', (user_id, bot_id)) as cursor:
            return await cursor.fetchone()
        
    
async def get_bot(bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM bots WHERE id = ?''', (bot_id,)) as cursor:
            return await cursor.fetchone()


async def get_all_bots():
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM bots''') as cursor:
            return await cursor.fetchall()
        
    
async def get_running_bots():
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM bots WHERE status = 'running' ''') as cursor:
            return await cursor.fetchall()
        

async def get_all_users():
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM users''') as cursor:
            return await cursor.fetchall()
        

async def get_all_constructor_users(bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM constructor_bots WHERE bot_id = ?''', (bot_id,)) as cursor:
            return await cursor.fetchall()

    
async def get_user_bots(user_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM bots WHERE user_id = ?''', (user_id,)) as cursor:
            return await cursor.fetchall()
        

async def get_text_button(button_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM text_buttons WHERE id = ?''', (button_id,)) as cursor:
            return await cursor.fetchone()


async def get_text_buttons(bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''SELECT * FROM text_buttons WHERE bot_id = ?''', (bot_id,)) as cursor:
            return await cursor.fetchall()


async def delete_bot(bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''DELETE FROM bots WHERE id = ?''', (bot_id,))
        await db.execute('''DELETE FROM constructor_bots WHERE bot_id = ?''', (bot_id,))
        await db.commit()


async def delete_text_buttons(bot_id):
    async with aiosqlite.connect('data/database/database.db') as db:
        await db.execute('''DELETE FROM text_buttons WHERE bot_id = ?''', (bot_id,))
        await db.commit()