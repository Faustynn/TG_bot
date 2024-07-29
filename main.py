import telebot
import sqlite3
import toml
import os
import logging
from logging.handlers import RotatingFileHandler

from telebot import types
from telebot.storage import StateMemoryStorage

# Настройка бота и хранилища состояния
config = toml.load('config.toml')
token = config['telegram']['key']
group_chat_id = config['telegram']['groupChat']

roles = toml.load('hight-roles.toml')['roles']


bot = telebot.TeleBot(token, state_storage=StateMemoryStorage())

# Словарь с переводами
translations = {
    'en': {
        'main_menu': 'Main Menu',
        'profile': '👤 Profile',
        'lang': '🏳️ Change language',
        'support': '⚙️ Support',
        'create_post': '✏️ Create post',
        'back': '🔙 Back',
        'start': 'Welcome, how can I help you today?',
        'main_menu_prompt': '👇 Main Menu 👇',
        'type_support': 'Choose the type of support:',
        'use_template': '🔍 Use template',
        'create_new_template': '🖊 Create template',
        'quick_post': '⚡ Quick post',
        'tech_support': 'Technical support',
        'community_support': 'Community support',
        'commercial_offer': 'Commercial offer',
        'choose_option_text': 'Choose an option:',
        'add_title_to_create_template': 'Please add a title to create a template:',
        'add_description_to_create_template': 'Please add a description as well:',
        'add_media_to_create_template': 'Add a photo or video if you want (if not, write "-"):',
        'success_add_template': 'Template created successfully!',
        'example_post_text': 'Example of your post:',
        'edit_post': '🖊 Edit template',
        'choose_edit': 'Choose what you want to edit:',
        'edit_title': 'Title',
        'edit_description': 'Description',
        'edit_media': 'Media Data',
        're_title': 'Enter a new title for the template:',
        're_description': 'Enter a new description for the template:',
        're_media': 'Add a photo or video if you want (if not, write "-"):',
        'success_edit_template': 'Template edited successfully',
        'delete_template': '🗑️ Delete template',
        're_delete': 'Are you sure you want to delete the template?',
        'success_delete_template': 'Template deleted successfully',
    },
    'ua': {
        'main_menu': 'Головне меню',
        'profile': '👤 Профіль',
        'lang': '🏳️ Змінити мову',
        'support': '⚙️ Підтримка',
        'create_post': '✏️ Створити пост',
        'back': '🔙 Назад',
        'start': 'Вітаю, чим я можу допомогти вам сьогодні?',
        'main_menu_prompt': '👇 Головне меню 👇',
        'type_support': 'Оберіть тип підтримки:',
        'use_template': '🔍 Використати шаблон',
        'create_new_template': '🖊 Створити шаблон',
        'quick_post': '⚡ Швидкий пост',
        'tech_support': 'Технічна підтримка',
        'community_support': 'Підтримка спільноти',
        'commercial_offer': 'Комерційна пропозиція',
        'choose_option_text': 'Оберіть опцію:',
        'add_title_to_create_template': 'Будь ласка, додайте назву для створення шаблону: ',
        'add_description_to_create_template': 'Додайте також опис:',
        'add_media_to_create_template': 'Додайте фото або відео за бажанням (якщо ні, напишіть "-")',
        'success_add_template': 'Шаблон створено успішно!',
        'example_post_text': 'Приклад вашого шаблону:',
        'edit_post': '🖊 Редагувати шаблон:',
        'choose_edit': 'Оберіть, що ви хочете відредагувати:',
        'edit_title': 'Назва',
        'edit_description': 'Опис',
        'edit_media': 'Медіа дані',
        're_title': 'Введіть нову назву шаблону:',
        're_description': 'Введіть новий опис шаблону:',
        're_media': 'Додайте фото або відео за бажанням (якщо ні, напишіть "-"):',
        'success_edit_template': 'Шаблон успішно відредаговано!',
        'delete_template': '🗑️ Видалити шаблон',
        're_delete': 'Ви впевнені, що хочете видалити шаблон?',
        'success_delete_template': 'Шаблон успішно видалено!',
    }
}

# Словарь для хранения выбранного языка и медиа
user_lang = {}
user_media = {}

def setup_logging() -> None:
    """
    Sets up global logging
    """
    # get root logger
    rootLogger = logging.getLogger("")
    # create a rotating file handler with 1 backup file and 1 megabyte size
    fileHandler = RotatingFileHandler(config["logging"]["path"], "wa", 1_000_000, 1, "UTF-8")
    # create a default console handler
    consoleHandler = logging.StreamHandler()
    # create a formatting style (modified from hikari)
    formatter = logging.Formatter(
        fmt="%(levelname)-1.1s %(asctime)23.23s %(name)s @ %(lineno)d: %(message)s"
    )
    # add the formatter to both handlers
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)
    # add both handlers to the root logger
    rootLogger.addHandler(fileHandler)
    rootLogger.addHandler(consoleHandler)
    # set logging level whatever
    rootLogger.setLevel(config["logging"]["level"])
    rootLogger.info("Set up logging!")

setup_logging()
logger = logging.getLogger(__name__)

# Функция для получения ID пользователя
def get_user_id(chat_id):
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0]
    else:
        logger.error(f"No user found with chat_id {chat_id}")
        raise ValueError(f"No user found with chat_id {chat_id}")


# Функция для создания таблиц
def setup_database():
    connection = sqlite3.connect(config['database']['path'])
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            login TEXT, 
            chat_id INTEGER UNIQUE, 
            status TEXT, 
            lang TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT NOT NULL,
            description TEXT, 
            media BLOB, 
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(chat_id)
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()


setup_database()


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id

    # Проверка наличия пользователя в базе данных
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    user = cursor.fetchone()

    if user:
        lang = user[4]  # получаем язык из базы данных
        user_lang[chat_id] = lang
        bot.send_message(chat_id, translations[lang]['start'])
        logger.info(f"Stared with an old user {message.from_user.first_name} (DB ID: {chat_id})")
        main_menu(chat_id)
    else:
        logger.info(f"Registred new user {message.from_user.first_name} (DB ID: {chat_id})")
        ask_language(chat_id)

    cursor.close()
    connection.close()


@bot.message_handler(commands=['getchat_id'])
def get_chat_id(message):
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    login = message.from_user.username
    chat_id = message.chat.id

    cursor.execute('SELECT status FROM users WHERE login = ?', ("@"+login,))
    role_row = cursor.fetchone()
    cursor.execute('SELECT chat_id FROM users WHERE login = ?', ("@"+login,))
    private_chat_id = cursor.fetchone()
    connection.close()


    if role_row:
        role = role_row[0]

        if role in ["ADMIN", "MODERATOR"]:
                bot.send_message(private_chat_id[0], f"ID чата: \"{chat_id}\"")
                bot.send_message(chat_id, f"Chat-ID send to private chat!")
    else:
        bot.send_message(chat_id, "You are not allowed to use this command!")

@bot.message_handler(commands=['update_roles'])
def update_roles(message):
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    login = message.from_user.username
    chat_id = message.chat.id

    cursor.execute('SELECT status FROM users WHERE login = ?', ("@" + login,))
    role_row = cursor.fetchone()

    role = role_row[0] if role_row else bot.send_message(chat_id, "You are not allowed to use this command!")

    if role in ["ADMIN", "MODERATOR"]:
        def update_user_roles(role_list, role_name):
            for user in role_list:
                cursor.execute("UPDATE users SET status = ? WHERE login = ?", (role_name, '@' + user))

        update_user_roles(roles['admins'], 'ADMIN')
        update_user_roles(roles['moderators'], 'MODERATOR')
        update_user_roles(roles['volunteers'], 'VOLUNTEER')

        connection.commit()
        cursor.close()
        connection.close()
        bot.send_message(message.chat.id, "Roles have been updated successfully!")


# Функция запроса выбора языка
def ask_language(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    btn1 = types.KeyboardButton('English 🇬🇧')
    btn2 = types.KeyboardButton('Українська 🇺🇦')
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "Please choose your language / Виберіть мову будь-ласка", reply_markup=markup)


# Обработчик выбора языка
@bot.message_handler(func=lambda message: message.text in ['English 🇬🇧', 'Українська 🇺🇦'])
def language_selection(message):
    chat_id = message.chat.id
    username = message.from_user.username
    username = '@' + username if username else '-'

    lang = 'en' if message.text == 'English 🇬🇧' else 'ua'
    user_lang[chat_id] = lang

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET login = ?, lang = ?, status = ? WHERE chat_id = ?',
                       (username, lang, 'USER', chat_id))
    else:
        cursor.execute('INSERT INTO users (login, chat_id, status, lang) VALUES (?, ?, ?, ?)',
                       (username, chat_id, 'USER', lang))

    connection.commit()
    cursor.close()
    connection.close()
    main_menu(chat_id)


# Главное меню
def main_menu(chat_id):
    lang = user_lang.get(chat_id, 'en')
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT status FROM users WHERE chat_id = ?', (chat_id,))
        role_row = cursor.fetchone()
        if not role_row:
            logger.error(f"Role {role_row} is not found!")
            bot.send_message(chat_id, "Error- Role not found!Please contact technical support!")
            return
        role = role_row[0]

        if role in ["ADMIN", "MODERATOR"]:
            btn1 = types.KeyboardButton(translations[lang]['create_post'])
            btn2 = types.KeyboardButton(translations[lang]['profile'])
            btn3 = types.KeyboardButton(translations[lang]['lang'])
            btn4 = types.KeyboardButton(translations[lang]['support'])
            markup.add(btn1,btn2, btn3, btn4)
        else:
            btn2 = types.KeyboardButton(translations[lang]['profile'])
            btn3 = types.KeyboardButton(translations[lang]['lang'])
            btn4 = types.KeyboardButton(translations[lang]['support'])
            markup.add(btn2, btn3, btn4)
        bot.send_message(chat_id, translations[lang]['main_menu_prompt'], reply_markup=markup)

    except sqlite3.Error as e:
        logger.error(f"DB error! {e}")
        bot.send_message(chat_id, f"Database error: {e}")
    finally:
        connection.close()


# Обработчик смены языка
@bot.message_handler(func=lambda message: message.text in [translations['en']['lang'], translations['ua']['lang']])
def change_language(message):
    ask_language(message.chat.id)


# Обработчик поддержки
@bot.message_handler(
    func=lambda message: message.text in [translations['en']['support'], translations['ua']['support']])
def support(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(translations[lang]['tech_support'], url="https://t.me/faustyyn"))
    markup.add(types.InlineKeyboardButton(translations[lang]['community_support'], url="https://t.me/faustyyn"))
    markup.add(types.InlineKeyboardButton(translations[lang]['commercial_offer'], url="https://t.me/faustyyn"))
    bot.send_message(chat_id, translations[lang]['type_support'], reply_markup=markup)


# Обработчик профиля
@bot.message_handler(
    func=lambda message: message.text in [translations['en']['profile'], translations['ua']['profile']])
def profile(message):
    chat_id = message.chat.id
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE chat_id = ?', (chat_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        if user[4] == 'ua':
            user_info = (
                f"➖➖➖➖➖➖➖➖➖➖➖\n"
                f"<b>Інформація про користувача:</b>\n"
                f"<b>Ім'я користувача:</b> <u>{user[1]}</u>\n"
                f"<b>Chat ID:</b> <u>{user[2]}</u>\n"
                f"<b>Статус:</b> {user[3]}\n"
                f"<b>Мова:</b> 🇺🇦\n"
                f"<i>Щоб змінити свій статус, зверніться до технічної підтримки</i>\n"
                f"➖➖➖➖➖➖➖➖➖➖➖"
            )
        else:
            user_info = (
                f"➖➖➖➖➖➖➖➖➖➖➖\n"
                f"<b>User Information:</b>\n"
                f"<b>Username:</b> <u>{user[1]}</u>\n"
                f"<b>Chat ID:</b> <u>{user[2]}</u>\n"
                f"<b>Status:</b> {user[3]}\n"
                f"<b>Language:</b> 🇬🇧\n"
                f"<i>Please contact technical support to change your status</i>\n"
                f"➖➖➖➖➖➖➖➖➖➖➖"
            )
    else:
        user_info = (
            f"➖➖➖➖➖➖➖➖➖➖➖\n"
            f"<b>User not found, please write to technical support! Error code: 404</b>\n"
            f"➖➖➖➖➖➖➖➖➖➖➖"
        )

    bot.send_message(chat_id, user_info, parse_mode='HTML')


quick = False
# Обработчик создания поста
@bot.message_handler(func=lambda message: message.text in [translations['en']['create_post'], translations['ua']['create_post']])
def create_post(message):
    global quick
    quick = False
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    btn0 = types.KeyboardButton(translations[lang]['back'])
    btn1 = types.KeyboardButton(translations[lang]['use_template'])
    btn2 = types.KeyboardButton(translations[lang]['create_new_template'])
    btn4 = types.KeyboardButton(translations[lang]['edit_post'])
    btn3 = types.KeyboardButton(translations[lang]['quick_post'])
    markup.add(btn0, btn1,btn4, btn2, btn3)
    bot.send_message(chat_id, translations[lang]['choose_option_text'], reply_markup=markup)

# Обработчик возврата в главное меню
@bot.message_handler(func=lambda message: message.text in [translations['en']['back'], translations['ua']['back']])
def back(message):
    main_menu(message.chat.id)


# Обработчик выбора шаблона
@bot.message_handler(func=lambda message: message.text in [translations['en']['use_template'], translations['ua']['use_template']])
def choose_template(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT id, title FROM posts WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)', (chat_id,))
    posts = cursor.fetchall()
    cursor.close()
    connection.close()

    if posts:
        markup = types.InlineKeyboardMarkup()
        for post in posts:
            markup.add(types.InlineKeyboardButton(post[1], callback_data=f"template_{post[0]}"))
        bot.send_message(chat_id, 'Please choose a template:', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'No templates have been created. Try creating a new template.')
        create_post(message)
@bot.callback_query_handler(func=lambda call: call.data.startswith('template_'))
def show_template(call):
    template_id = call.data.split('_')[1]
    chat_id = call.message.chat.id
 #   print(template_id, chat_id)
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT title, description, media FROM posts WHERE id = ?', (template_id,))
    post = cursor.fetchone()
    cursor.close()
    connection.close()

    if post:
        title, description, media = post

        title = escape_markdown(title)
        description = escape_markdown(description)

        response = (f"*\"{title}\"*\n\n"
                    f"{description}")
        if media:
            if media.endswith(('.png', '.jpg', '.jpeg')):
                bot.send_photo(group_chat_id, open(media, 'rb'), caption=response, parse_mode='MarkdownV2')
            elif media.endswith('.mp4'):
                bot.send_video(group_chat_id, open(media, 'rb'), caption=response, parse_mode='MarkdownV2')
            else:
                bot.send_message(group_chat_id, response, parse_mode='MarkdownV2')
        else:
            bot.send_message(group_chat_id, response, parse_mode='MarkdownV2')
    else:
        bot.send_message(chat_id, 'Error: Template not found, try again!')

@bot.message_handler(func=lambda message: message.text in [translations['en']['quick_post'], translations['ua']['quick_post']])
def quick_post(message):
    global quick
    quick = True
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')
    bot.send_message(chat_id, translations[lang]['add_title_to_create_template'])
    bot.register_next_step_handler(message, get_title)


@bot.message_handler(func=lambda message: message.text in [translations['en']['edit_post'], translations['ua']['edit_post']])
def edit_post(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT id, title FROM posts WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)', (chat_id,))
    posts = cursor.fetchall()
    cursor.close()
    connection.close()

    if posts:
        markup = types.InlineKeyboardMarkup()
        for post in posts:
            markup.add(types.InlineKeyboardButton(post[1], callback_data=f"edit_{post[0]}"))
        bot.send_message(chat_id, 'Please choose a template to edit:', reply_markup=markup)
    else:
        bot.send_message(chat_id, 'No templates have been created. Try creating a new template.')
        create_post(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_'))
def edit_template(call):
    template_id = call.data.split('_')[1]
    chat_id = call.message.chat.id

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT title, description, media FROM posts WHERE id = ?', (template_id,))
    post = cursor.fetchone()
    cursor.close()
    connection.close()

    if post:
        title, description, media = post
        user_data[chat_id] = {'template_id': template_id, 'title': title, 'description': description, 'media': media}
        lang = user_lang.get(chat_id, 'en')

        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        btn0 = types.KeyboardButton(translations[lang]['back'])
        btn1 = types.KeyboardButton(translations[lang]['edit_title'])
        btn2 = types.KeyboardButton(translations[lang]['edit_description'])
        btn3 = types.KeyboardButton(translations[lang]['edit_media'])
        btn4 = types.KeyboardButton(translations[lang]['delete_template'])
        markup.add(btn0, btn1, btn2, btn3, btn4)
        bot.send_message(chat_id, translations[lang]['choose_edit'], reply_markup=markup)
        bot.register_next_step_handler(call.message, edit_template_step)
    else:
        bot.send_message(chat_id, translations[user_lang.get(chat_id, 'en')]['error_template_not_found'])

def edit_template_step(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    if message.text == translations[lang]['edit_title']:
        bot.send_message(chat_id, translations[lang]['re_title'])
        bot.register_next_step_handler(message, edit_title)
    elif message.text == translations[lang]['edit_description']:
        bot.send_message(chat_id, translations[lang]['re_description'])
        bot.register_next_step_handler(message, edit_description)
    elif message.text == translations[lang]['edit_media']:
        bot.send_message(chat_id, translations[lang]['re_media'])
        bot.register_next_step_handler(message, edit_media)
    elif message.text == translations[lang]['delete_template']:
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
        btn_yes = types.KeyboardButton('YES')
        btn_no = types.KeyboardButton('NO')
        markup.add(btn_yes, btn_no)
        bot.send_message(chat_id, translations[lang]['re_delete'], reply_markup=markup)
        bot.register_next_step_handler(message, confirm_delete_template)
    elif message.text == translations[lang]['back']:
        create_post(message)
    else:
        bot.send_message(chat_id, translations[lang]['error_invalid_option'])


def confirm_delete_template(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    if message.text.upper() == 'YES':
        if chat_id in user_data and 'template_id' in user_data[chat_id]:
            template_id = user_data[chat_id]['template_id']
            connection = sqlite3.connect('database.sql')
            cursor = connection.cursor()
            cursor.execute('DELETE FROM posts WHERE id = ?', (template_id,))
            connection.commit()
            cursor.close()
            connection.close()
            bot.send_message(chat_id, translations[lang]['success_delete_template'])
        else:
            bot.send_message(chat_id, 'Error: Template not found, try again!')
    elif message.text.upper() == 'NO':
        bot.send_message(chat_id, 'Deletion canceled.')
    create_post(message)

def edit_title(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')
    new_title = message.text

    if chat_id not in user_data or 'template_id' not in user_data[chat_id]:
        bot.send_message(chat_id, translations[lang]['error_no_template_selected'])
        return

    template_id = user_data[chat_id]['template_id']

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('UPDATE posts SET title = ? WHERE id = ?', (new_title, template_id))
    connection.commit()
    cursor.close()
    connection.close()

    bot.send_message(chat_id, translations[lang]['success_edit_template'])
    create_post(message)

def edit_description(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')
    new_description = message.text

    if chat_id not in user_data or 'template_id' not in user_data[chat_id]:
        bot.send_message(chat_id, translations[lang]['error_no_template_selected'])
        return

    template_id = user_data[chat_id]['template_id']

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('UPDATE posts SET description = ? WHERE id = ?', (new_description, template_id))
    connection.commit()
    cursor.close()
    connection.close()

    bot.send_message(chat_id, translations[lang]['success_edit_template'])
    create_post(message)

def edit_media(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    if message.content_type == 'text':
        media = message.text
        user_data[chat_id]['media'] = None if media == "-" else bot.send_message(chat_id, translations[lang]['add_media_to_create_template'])
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id  # получаем фото
        file_info = bot.get_file(file_id)
        media = save_photo(file_info, file_id)
        user_data[chat_id]['media'] = media
    elif message.content_type == 'video':
        file_id = message.video.file_id  # получаем видео
        file_info = bot.get_file(file_id)
        media = save_video(file_info, file_id)
        user_data[chat_id]['media'] = media
    else:
        bot.send_message(chat_id, "Unsupported media type. Please upload photo or video.")


    user_id = get_user_id(chat_id)
    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('UPDATE posts SET media = ? WHERE user_id = ?', (media, user_id))
    connection.commit()
    cursor.close()
    connection.close()

    bot.send_message(chat_id, translations[lang]['success_edit_template'])
    create_post(message)



user_data = {}
# Обработчик создания нового шаблона
@bot.message_handler(func=lambda message: message.text in [translations['en']['create_new_template'],translations['ua']['create_new_template']])
def handle_create_new_template(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    connection = sqlite3.connect('database.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT status FROM users WHERE chat_id = ?', (chat_id,))
    role_row = cursor.fetchone()
    role = role_row[0] if role_row else 'USER'
    cursor.execute('SELECT COUNT(*) FROM posts WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)', (chat_id,))
    templates_row = cursor.fetchone()
    number_of_templates = templates_row[0] if templates_row else 0
    connection.close()

    if ((number_of_templates < 10 and (role == "VOLUNTEER" or role == "MODERATOR")) or (number_of_templates < 6 and role == "MODERATOR") or (number_of_templates < 2 and role == "USER") or (role == "ADMIN")):
        bot.send_message(chat_id, translations[lang]['add_title_to_create_template'])
        bot.register_next_step_handler(message, get_title)
    else:
        bot.send_message(chat_id, f"You have reached the limit of templates! ({number_of_templates})")
# Функция для экранирования спецсимволов
def escape_markdown(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])
def get_title(message):
    chat_id = message.chat.id
    title = message.text
    user_data[chat_id] = {'title': title}
    lang = user_lang.get(chat_id, 'en')
    bot.send_message(chat_id, translations[lang]['add_description_to_create_template'])
    bot.register_next_step_handler(message, get_description)
def get_description(message):
    chat_id = message.chat.id
    description = message.text
    user_data[chat_id]['description'] = description
    lang = user_lang.get(chat_id, 'en')
    bot.send_message(chat_id, translations[lang]['add_media_to_create_template'])
    bot.register_next_step_handler(message, get_media)
def get_media(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'en')

    if message.content_type == 'text':
        media = message.text
        user_data[chat_id]['media'] = None if media == "-" else bot.send_message(chat_id, translations[lang]['add_media_to_create_template'])
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id  # получаем фото
        file_info = bot.get_file(file_id)
        media = save_photo(file_info, file_id)
        user_data[chat_id]['media'] = media
    elif message.content_type == 'video':
        file_id = message.video.file_id  # получаем видео
        file_info = bot.get_file(file_id)
        media = save_video(file_info, file_id)
        user_data[chat_id]['media'] = media
    else:
        bot.send_message(chat_id, "Unsupported media type. Please upload photo or video.")

    user_id = get_user_id(chat_id)
    title = user_data[chat_id]['title']
    description = user_data[chat_id]['description']
    media = user_data[chat_id]['media']
    if(quick == False):
        with sqlite3.connect('database.sql') as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO posts (title, description, media, user_id) VALUES (?, ?, ?, ?)',
                           (title, description, media, user_id))
            connection.commit()

        bot.send_message(chat_id, translations[lang]['success_add_template'])
    else:
        title = escape_markdown(title)
        description = escape_markdown(description)

        response = (f"*\"{title}\"*\n\n"
                    f"{description}")
        if media:
            if media.endswith(('.png', '.jpg', '.jpeg')):
                bot.send_photo(group_chat_id, open(media, 'rb'), caption=response, parse_mode='MarkdownV2')
            elif media.endswith('.mp4'):
                bot.send_video(group_chat_id, open(media, 'rb'), caption=response, parse_mode='MarkdownV2')
            else:
                bot.send_message(group_chat_id, response, parse_mode='MarkdownV2')
        else:
            bot.send_message(group_chat_id, response, parse_mode='MarkdownV2')


    user_data.pop(chat_id)
    create_post(message)
def save_photo(file_info, file_id):
    valid_extensions = ['.png', '.jpg', '.jpeg']
    _, file_extension = os.path.splitext(file_info.file_path)

    if file_extension.lower() not in valid_extensions:
        return "Невозможный формат. Пожалуйста, загрузите файл в формате PNG или JPEG."

    # Создаем папку, если она не существует
    if not os.path.exists('photos'):
        os.makedirs('photos')

    file_path = os.path.join('photos', f'{file_id}{file_extension}')
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    return file_path
def save_video(file_info, file_id):
    valid_extensions = ['.mp4']
    _, file_extension = os.path.splitext(file_info.file_path)

    if file_extension.lower() not in valid_extensions:
        return "Невозможный формат. Пожалуйста, загрузите файл в формате MP4."

    # Создаем папку, если она не существует
    if not os.path.exists('videos'):
        os.makedirs('videos')

    file_path = os.path.join('videos', f'{file_id}{file_extension}')
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    return file_path






bot.polling(none_stop=True)
