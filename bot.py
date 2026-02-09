import logging
import os
import requests
import feedparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Константы (берутся из настроек сервера для безопасности)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ABACUS_API_KEY = os.getenv("ABACUS_API_KEY")
CHANNEL_ID = "@h2_nation" # Замените на юзернейм вашего канала

# Ключевые слова для поиска новостей
SEARCH_QUERIES = [
    "hydrogen water health benefits",
    "molecular hydrogen therapy",
    "hydrogen inhalation medicine"
]

def get_hydrogen_news():
    news_items = []
    for query in SEARCH_QUERIES:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news_items.append({"title": entry.title, "link": entry.link})
    return news_items

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я ваш H2-ассистент. Используйте /fetch, чтобы собрать новости за неделю.")

def fetch_news(update: Update, context: CallbackContext):
    news = get_hydrogen_news()
    context.user_data['current_news'] = news
    
    keyboard = []
    for i, item in enumerate(news):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {item['title'][:50]}...", callback_data=str(i))])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Вот свежие новости по водороду. Выберите одну для создания поста:", reply_markup=reply_markup)

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    news_idx = int(query.data)
    selected_news = context.user_data['current_news'][news_idx]
    
    # Запрос к Abacus RouteLLM для генерации поста
    headers = {"Authorization": f"Bearer {ABACUS_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Напиши вдохновляющий пост для Telegram канала 'Нация на водороде' на основе этой новости: {selected_news['title']}. Ссылка: {selected_news['link']}. Стиль: лайфстайл, польза для здоровья, доступно. Используй эмодзи."
    
    payload = {
        "model": "gpt-4o", # Можно заменить на нужную модель
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post("https://routellm.abacus.ai/v1/chat/completions", headers=headers, json=payload)
    post_text = response.json()['choices'][0]['message']['content']
    
    context.user_data['pending_post'] = post_text
    
    keyboard = [[InlineKeyboardButton("✅ Опубликовать в канал", callback_data="publish")]]
    query.edit_message_text(text=f"Предпросмотр поста:\n\n{post_text}", reply_markup=InlineKeyboardMarkup(keyboard))

def publish_post(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    post_text = context.user_data.get('pending_post')
    context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
    query.edit_message_text(text="🚀 Пост опубликован в канале 'Нация на водороде'!")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("fetch", fetch_news))
    dp.add_handler(CallbackQueryHandler(button_click, pattern='^[0-9]$'))
    dp.add_handler(CallbackQueryHandler(publish_post, pattern='^publish$'))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()