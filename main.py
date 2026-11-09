import os
import threading
from flask import Flask
import telebot

# Инициализация Flask для поддержания работоспособности на Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Считывание переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, f"Привет! Бот успешно запущен и работает в облаке 24/7.")

if __name__ == "__main__":
    # Запуск веб-сервера в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Запуск непрерывного опроса Telegram API
    print("Бот успішно запущено...")
    bot.infinity_polling(skip_pending=True)
