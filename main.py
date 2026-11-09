# -*- coding: utf-8 -*- 
import os
import threading
import time
from flask import Flask
import telebot
from telebot import types
import sqlite3
from requests.exceptions import ReadTimeout, ConnectionError

# --- FLASK SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- НАЛАШТУВАННЯ ---
TOKEN = os.environ.get("BOT_TOKEN", '8584299667:AAEmH44ZUQbvX4YJDeRo_W-cIemaiIURniM')
ADMIN_ID = int(os.environ.get("ADMIN_ID", 6503705720))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", 'AkylaRC')

bot = telebot.TeleBot(TOKEN)

# --- ІНІЦІАЛІЗАЦІЯ БАЗИ ДАНИХ ---
def init_db():
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    
    q.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR,
            name VARCHAR,
            amount VARCHAR,
            ref_user VARCHAR,
            ref_count VARCHAR,
            ref_donate VARCHAR
        )
    ''')
    
    q.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id VARCHAR,
            karta VARCHAR,
            qiwi VARCHAR,
            bitcoin TEXT
        )
    ''')
    
    q.execute('''
        CREATE TABLE IF NOT EXISTS product_photos (
            city VARCHAR,
            district VARCHAR,
            tovar VARCHAR,
            file_id TEXT,
            PRIMARY KEY (city, district, tovar)
        )
    ''')

    q.execute('SELECT COUNT(*) FROM config WHERE id = 1')
    if q.fetchone()[0] == 0:
        q.execute("INSERT INTO config (id, karta, qiwi, bitcoin) VALUES ('1', '4149 0000 0000 0000', 'qiwi_wallet_or_phone', 'bc1qexamplebitcoinwallet')")
    
    connection.commit()
    connection.close()

init_db()

# --- КЛАВІАТУРИ ---
keyboardMain = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
keyboardMain.add(
    types.KeyboardButton('🏙 129-й квартал'),
    types.KeyboardButton('🏙 мкрн. Зарічний'),
    types.KeyboardButton('🏙 Пруди'),
    types.KeyboardButton('🛠 Завантажити фото товару (Адмін)')
)

kryvyi_rih_rayons = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
kryvyi_rih_rayons.row('🔹 129-й квартал', '🔹 Зарічний')
kryvyi_rih_rayons.row('🔹 Пруди')
kryvyi_rih_rayons.row('🔹 Головна')

# Меню товаров без указания цены
tovar_list = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
tovar_list.row('🧪 Проба солі {0.1г-0.2г}')
tovar_list.row('🔹 Головна')

oplata = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
oplata.row('💳 Картка', '₿ Bitcoin')
oplata.row('🔹 Головна')

oplata_oplatil = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
oplata_oplatil.row('✅ Оплатив', '❌ Скасувати')

admin_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
admin_kb.row('💳 Змінити Картку', '₿ Змінити Bitcoin')
admin_kb.row('👥 Кількість користувачів', '🛠 Завантажити фото товару (Адмін)')
admin_kb.row('🔹 Головна')

user_selected_tovar = {}
user_selected_city = {}
user_selected_rayon = {}
admin_temp_data = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.id == ADMIN_ID:
        file_id = message.photo[-1].file_id
        if ADMIN_ID in admin_temp_data and admin_temp_data[ADMIN_ID].get('step') == 'wait_photo':
            city = admin_temp_data[ADMIN_ID]['city']
            rayon = admin_temp_data[ADMIN_ID]['rayon']
            tovar = admin_temp_data[ADMIN_ID]['tovar']
            
            connection = sqlite3.connect('database.sqlite')
            q = connection.cursor()
            q.execute('''
                INSERT OR REPLACE INTO product_photos (city, district, tovar, file_id) 
                VALUES (?, ?, ?, ?)
            ''', (city, rayon, tovar, file_id))
            connection.commit()
            connection.close()
            
            admin_temp_data.pop(ADMIN_ID, None)
            bot.reply_to(message, f"✨ <b>Фото успішно прив'язано!</b>\n\n🏙 Місто: {city}\n📍 Район: {rayon}\n📦 Товар: {tovar}\n🆔 File ID: <code>{file_id}</code>", parse_mode='HTML', reply_markup=admin_kb)
        else:
            bot.reply_to(message, f"🆔 ID цього фото:\n\n<code>{file_id}</code>", parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start_message(message):
    userid = str(message.chat.id)
    username = str(message.from_user.username) if message.from_user.username else "NoUsername"
    ref_text = message.text
    ref_code = ref_text[7:] if len(ref_text) > 7 else ''

    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute('SELECT * FROM users WHERE id IS ?', (userid,))
    row = q.fetchone()

    if row is None:
        q.execute("INSERT INTO users (id, name, amount, ref_user, ref_count, ref_donate) VALUES (?, ?, ?, ?, ?, ?)", 
                  (userid, username, '0', ref_code, '0', '0'))
        connection.commit()
        if ref_code != '':
            q.execute("UPDATE users SET ref_count = ref_count + 1 WHERE id = ?", (ref_code,))
            connection.commit()
    connection.close()

welcome_text = (
        "💎 <b>Вітаємо у нашому сервісі!</b> 💎\n\n"
        "📍 <i>Місто: Кривий Ріг</i>\n\n"
        "<b>📋 Інструкція для замовлення:</b>\n"
        " <b>1️⃣</b> Виберіть потрібний район на клавіатурі нижче.\n"
        " <b>2️⃣</b> Оберіть бажаний товар та спосіб оплати.\n"
        " <b>3️⃣</b> Здійсніть оплату <u>суворо з правильним коментарем</u>.\n"
        " <b>4️⃣</b> Натисніть кнопку «Оплатив» — бот надішле вам повну інформацію (фото зблизька, здалеку та координати).\n\n"
        "⚠️ <b>ВАЖЛИВЕ ПРАВИЛО ЩОДО ПЗ:</b>\n"
        "<i>Якщо ви хочете отримати ПЗ, перед розкопками (за 10 метрів від кладу) починайте знімати відео, щоб на ньому було добре видно всі орієнтири. Буде відео — буде і ПЗ, без відео навіть не просіть ПЗ!</i>\n\n"
        "✨ <i>Бажаємо приємного відпочинку! Виберіть район для початку:</i>"
    )

    bot.send_message(
        message.chat.id, 
        welcome_text,
        parse_mode='HTML', 
        reply_markup=keyboardMain
    )

@bot.message_handler(content_types=['text'])
def send_text(message):
    text = message.text.lower()
    chat_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"

    if text == '✅ оплатив':
        tovar = user_selected_tovar.get(chat_id, '')
        city = user_selected_city.get(chat_id, 'Кривий Ріг')
        rayon = user_selected_rayon.get(chat_id, '')

        if not tovar or not rayon:
            bot.send_message(chat_id, '⚠️ <b>Час сесії минув або дані втрачені.</b> Будь ласка, почніть спочатку з /start', parse_mode='HTML', reply_markup=keyboardMain)
            return

        bot.send_message(chat_id, '⏳ <b>Ваш платіж успішно передано адміністратору на перевірку.</b>\nЯк тільки кошти надійдуть, бот надішле вам замовлення у цей чат!', parse_mode='HTML', reply_markup=keyboardMain)

        markup = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton("✅ Підтвердити оплату", callback_data=f"app_{chat_id}")
        btn_no = types.InlineKeyboardButton("❌ Відхилити", callback_data=f"rej_{chat_id}")
        markup.add(btn_yes, btn_no)

        admin_notification = (
            f"🔔 <b>Нова заявка на оплату!</b>\n\n"
            f"👤 Користувач: {username} (<code>{chat_id}</code>)\n"
            f"🏙 Місто: {city}\n"
            f"📍 Район: {rayon}\n"
            f"📦 Товар: <b>{tovar}</b>"
        )

        bot.send_message(
            ADMIN_ID,
            admin_notification,
            parse_mode='HTML',
            reply_markup=markup
        )

        user_selected_tovar.pop(chat_id, None)
        user_selected_city.pop(chat_id, None)
        user_selected_rayon.pop(chat_id, None)

    elif text == '🔹 головна':
        user_selected_tovar.pop(chat_id, None)
        user_selected_city.pop(chat_id, None)
        user_selected_rayon.pop(chat_id, None)
        bot.send_message(chat_id, '🏠 <b>Головне меню</b>\nВиберіть район:', parse_mode='HTML', reply_markup=keyboardMain)

    elif text == '❌ скасувати':
        user_selected_tovar.pop(chat_id, None)
        user_selected_city.pop(chat_id, None)
        user_selected_rayon.pop(chat_id, None)
        bot.send_message(chat_id, '❌ <b>Замовлення скасовано.</b> Повернення до головного меню.', parse_mode='HTML', reply_markup=keyboardMain)

    elif text == 'адмін' and chat_id == ADMIN_ID:
        bot.send_message(chat_id, '🛠 <b>Панель адміністратора</b> активована.', parse_mode='HTML', reply_markup=admin_kb)

    elif text in ['завантажити фото товару (адмін)', '🛠 завантажити фото товару (адмін)'] and chat_id == ADMIN_ID:
        admin_temp_data[ADMIN_ID] = {'city': 'Кривий Ріг'}
        msg = bot.send_message(chat_id, '📍 <b>Виберіть район для завантаження фото:</b>', parse_mode='HTML', reply_markup=kryvyi_rih_rayons)
        bot.register_next_step_handler(msg, admin_set_rayon_from_menu)

    elif text == '👥 кількість користувачів' and chat_id == ADMIN_ID:
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute("SELECT COUNT(id) FROM users")
        stata_users = str(q.fetchone()[0])
        connection.close()
        bot.send_message(chat_id, f'📈 <b>Статистика:</b>\nЗагалом користувачів у боті: <b>{stata_users}</b>', parse_mode='HTML', reply_markup=admin_kb)

    elif text == '💳 змінити картку' and chat_id == ADMIN_ID:
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute('SELECT karta FROM config WHERE id = 1')
        karta = q.fetchone()[0]
        connection.close()
        msg = bot.send_message(chat_id, f'💳 Поточна картка: <code>{karta}</code>\n\nВведіть нові реквізити картки:', parse_mode='HTML')
        bot.register_next_step_handler(msg, admin_new_karta)

    elif text == '₿ змінити bitcoin' and chat_id == ADMIN_ID:
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute('SELECT bitcoin FROM config WHERE id = 1')
        bitcoin = q.fetchone()[0]
        connection.close()
        msg = bot.send_message(chat_id, f'₿ Поточний Bitcoin гаманець: <code>{bitcoin}</code>\n\nВведіть новий гаманець:', parse_mode='HTML')
        bot.register_next_step_handler(msg, admin_new_bitcoin)

    elif text in ['🏙 129-й квартал', '🔹 129-й квартал']:
        user_selected_city[chat_id] = 'Кривий Ріг'
        user_selected_rayon[chat_id] = '129-й квартал'
        msg = bot.send_message(chat_id, '📦 <b>Обрано район:</b> 129-й квартал\n\n⬇️ <b>Виберіть позицію:</b>', parse_mode='HTML', reply_markup=tovar_list)
        bot.register_next_step_handler(msg, what_tovar)

    elif text in ['🏙 мкрн. зарічний', '🔹 зарічний']:
        user_selected_city[chat_id] = 'Кривий Ріг'
        user_selected_rayon[chat_id] = 'мкрн. Зарічний'
        msg = bot.send_message(chat_id, '📦 <b>Обрано район:</b> мкрн. Зарічний\n\n⬇️ <b>Виберіть позицію:</b>', parse_mode='HTML', reply_markup=tovar_list)
        bot.register_next_step_handler(msg, what_tovar)

    elif text in ['🏙 пруди', '🔹 пруди']:
        user_selected_city[chat_id] = 'Кривий Ріг'
        user_selected_rayon[chat_id] = 'Пруди'
        msg = bot.send_message(chat_id, '📦 <b>Обрано район:</b> Пруди\n\n⬇️ <b>Виберіть позицію:</b>', parse_mode='HTML', reply_markup=tovar_list)
        bot.register_next_step_handler(msg, what_tovar)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message.chat.id != ADMIN_ID:
        return

    data = call.data
    parts = data.split('_')
    action = parts[0]
    target_user_id = int(parts[1])

    if action == 'app':
        text_lines = call.message.text.split('\n')
        city, rayon, tovar = "Кривий Ріг", "", ""
        
        for line in text_lines:
            if "Район:" in line:
                rayon = line.split("Район:")[1].strip()
            elif "Товар:" in line:
                tovar = line.replace("<b>", "").replace("</b>", "").split("Товар:")[1].strip()

        photo_data = ''
        connection = sqlite3.connect('database.sqlite')
        q = connection.cursor()
        q.execute("SELECT file_id FROM product_photos WHERE city = ? AND district = ? AND tovar = ?", (city, rayon, tovar))
        res = q.fetchone()
        connection.close()
        if res:
            photo_data = res[0]

        try:
            bot.send_message(target_user_id, '🎉 <b>Оплату успішно підтверджено адміністратором!</b>\nВаші дані замовлення:', parse_mode='HTML')
            if not photo_data:
                bot.send_message(target_user_id, f'📦 Товар: <b>{tovar}</b>\n🏙 Місто: {city}\n📍 Район: {rayon}\n\n⚠️ <i>Фото для цієї позиції ще завантажується адміністратором, очікуйте надішлем сюди ж.</i>', parse_mode='HTML', reply_markup=keyboardMain)
            else:
                bot.send_photo(target_user_id, photo_data, caption=f'📦 Товар: <b>{tovar}</b>\n🏙 Місто: {city}\n📍 Район: {rayon}\n\n✅ <b>Координати та фото успішно завантажено. Гарного відпочинку!</b>', parse_mode='HTML', reply_markup=keyboardMain)
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ Помилка надсилання користувачу: {e}")

        bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=call.message.text + "\n\n<b>✅ СТАТУС: Оплату підтверджено</b>", parse_mode='HTML')

    elif action == 'rej':
        try:
            bot.send_message(target_user_id, '❌ <b>Вашу оплату було відхилено адміністратором.</b>\nЯкщо сталася помилка, будь ласка, зверніться до підтримки.', parse_mode='HTML', reply_markup=keyboardMain)
        except:
            pass

        bot.edit_message_text(chat_id=ADMIN_ID, message_id=call.message.message_id, text=call.message.text + "\n\n<b>❌ СТАТУС: Оплату відхилено</b>", parse_mode='HTML')

def admin_set_rayon_from_menu(message):
    if message.text.lower() == '🔹 головна' or message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'Скасовано.', reply_markup=admin_kb)
        return
    rayon = message.text.strip().replace('🔹 ', '')
    admin_temp_data[ADMIN_ID]['rayon'] = rayon
    msg = bot.send_message(message.chat.id, f'📍 Район: <b>{rayon}</b>.\n\nТепер виберіть товар з каталогу нижче:', parse_mode='HTML', reply_markup=tovar_list)
    bot.register_next_step_handler(msg, admin_set_tovar)

def admin_set_tovar(message):
    if message.text.lower() == '🔹 головна' or message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, 'Скасовано.', reply_markup=admin_kb)
        return
    tovar = message.text.strip()
    admin_temp_data[ADMIN_ID]['tovar'] = tovar
    admin_temp_data[ADMIN_ID]['step'] = 'wait_photo'
    bot.send_message(message.chat.id, f"📸 Надішліть **фотографію** для цього товару в обраному районі:", parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())

def what_tovar(message):
    chat_id = message.chat.id
    chosen_tovar = message.text
    if chosen_tovar.lower() == '🔹 головна':
        bot.send_message(chat_id, '🏠 Повернення на головну', reply_markup=keyboardMain)
        return
    
    if 'проба солі' in chosen_tovar.lower():
        markup = types.InlineKeyboardMarkup()
        btn_profile = types.InlineKeyboardButton("📩 Звернутися за пробою", url=f"https://t.me/{ADMIN_USERNAME}")
        markup.add(btn_profile)
        
        bot.send_message(
            chat_id, 
            f"🧪 <b>Оформлення проби солі (0.1г-0.2г)</b>\n\n"
            f"Щоб отримати пробу, будь ласка, переходьте одразу до менеджера в особисті повідомлення за кнопкою нижче:",
            parse_mode='HTML',
            reply_markup=markup
        )
        bot.send_message(chat_id, '🏠 Повернення до головного меню:', reply_markup=keyboardMain)
        return

    user_selected_tovar[chat_id] = chosen_tovar
    msg = bot.send_message(chat_id, '💳 <b>Виберіть зручний спосіб оплати:</b>', parse_mode='HTML', reply_markup=oplata)
    bot.register_next_step_handler(msg, what_oplata)

def what_oplata(message):
    chat_id = message.chat.id
    pay_method = message.text
    if chat_id not in user_selected_tovar or not user_selected_tovar[chat_id]:
        user_selected_tovar[chat_id] = '🧪 Проба солі {0.1г-0.2г}'
    chosen_tovar = user_selected_tovar.get(chat_id)

    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("SELECT karta, bitcoin FROM config WHERE id = 1")
    cfg = q.fetchone()
    q.execute("SELECT ref_user FROM users WHERE id = ?", (str(chat_id),))
    res = q.fetchone()
    connection.close()

    karta = cfg[0] if cfg else 'Не вказано'
    bitcoin = cfg[1] if cfg else 'Не вказано'
    ref_user_val = res[0] if res and res[0] else str(chat_id)

    if 'картка' in pay_method.lower():
        payment_text = (
            f"🛒 <b>Ваше замовлення:</b>\n"
            f"👉 <b>{chosen_tovar}</b>\n\n"
            f"💳 <b>Реквізити картки:</b>\n<code>{karta}</code>\n\n"
            f"💬 <b>Обов'язковий коментар до платежу:</b> <code>{ref_user_val}</code>\n\n"
            f"⚠️ <i>Оплачуйте точну суму та обов'язково вказуйте коментар! Після оплати натисніть кнопку «Оплатив» нижче.</i>"
        )
        bot.send_message(chat_id, payment_text, parse_mode='HTML', reply_markup=oplata_oplatil)
    elif 'bitcoin' in pay_method.lower():
        payment_text = (
            f"🛒 <b>Ваше замовлення:</b>\n"
            f"👉 <b>{chosen_tovar}</b>\n\n"
            f"₿ <b>Bitcoin гаманець:</b>\n<code>{bitcoin}</code>\n\n"
            f"💬 <b>Коментар / Memo:</b> <code>{ref_user_val}</code>\n\n"
            f"⚠️ <i>Після здійснення транзакції натисніть кнопку «Оплатив» нижче.</i>"
        )
        bot.send_message(chat_id, payment_text, parse_mode='HTML', reply_markup=oplata_oplatil)
    else:
        bot.send_message(chat_id, '🏠 Повернення на головну', reply_markup=keyboardMain)

def admin_new_karta(message):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("UPDATE config SET karta = ? WHERE id = 1", (message.text,))
    connection.commit()
    connection.close()
    bot.send_message(message.chat.id, '✅ Картку успішно оновлено!', reply_markup=admin_kb)

def admin_new_bitcoin(message):
    connection = sqlite3.connect('database.sqlite')
    q = connection.cursor()
    q.execute("UPDATE config SET bitcoin = ? WHERE id = 1", (message.text,))
    connection.commit()
    connection.close()
    bot.send_message(message.chat.id, '✅ Bitcoin гаманець успішно оновлено!', reply_markup=admin_kb)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке для связки с Render
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Бот успішно запущено...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except (ReadTimeout, ConnectionError):
            print("⚠️ Втрачено з'єднання з Telegram. Перепідключення через 5 секунд...")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Виникла непередбачувана помилка: {e}")
            time.sleep(5)
