import logging
import os
import requests
import feedparser
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ABACUS_API_KEY = os.getenv("ABACUS_API_KEY")
CHANNEL_ID = "@h2_nation" 

def get_hydrogen_news():
    news_items = []
    queries = ["hydrogen water health benefits", "molecular hydrogen therapy"]
    for query in queries:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news_items.append({"title": entry.title, "link": entry.link})
    return news_items

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ваш H2-ассистент. Используйте /fetch для новостей.")

async def fetch_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = get_hydrogen_news()
    context.user_data['current_news'] = news
    keyboard = [[InlineKeyboardButton(f"{i+1}. {item['title'][:50]}...", callback_data=str(i))] for i, item in enumerate(news)]
    await update.message.reply_text("Выберите новость:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    news_idx = int(query.data)
    selected_news = context.user_data['current_news'][news_idx]
    
    headers = {"Authorization": f"Bearer {ABACUS_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Напиши вдохновляющий пост для Telegram канала на основе новости: {selected_news['title']}. Ссылка: {selected_news['link']}. Стиль: лайфстайл, польза для здоровья. Используй эмодзи."
    
    response = requests.post("https://routellm.abacus.ai/v1/chat/completions", headers=headers, json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}]
    })
    post_text = response.json()['choices'][0]['message']['content']
    context.user_data['pending_post'] = post_text
    keyboard = [[InlineKeyboardButton("✅ Опубликовать", callback_data="publish")]]
    await query.edit_message_text(text=f"Предпросмотр:\n\n{post_text}", reply_markup=InlineKeyboardMarkup(keyboard))

async def publish_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(chat_id=CHANNEL_ID, text=context.user_data.get('pending_post'))
    await query.edit_message_text(text="🚀 Опубликовано!")

if __name__ == '__main__':
    # Новый способ запуска, который обходит ошибку Python 3.13
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fetch", fetch_news))
    application.add_handler(CallbackQueryHandler(button_click, pattern='^[0-9]$'))
    application.add_handler(CallbackQueryHandler(publish_post, pattern='^publish$'))
    
    print("Бот запущен...")
    application.run_polling(close_loop=False)
