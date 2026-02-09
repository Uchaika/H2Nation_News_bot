import logging
import os
import requests
import feedparser
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("ABACUS_API_KEY")
CHANNEL = "@h2_nation" 

def get_news():
    items = []
    url = "https://news.google.com/rss/search?q=hydrogen+water+health&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    for entry in feed.entries[:5]:
        items.append({"title": entry.title, "link": entry.link})
    return items

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text("Бот активен. Напишите /fetch")

async def fetch(u: Update, c: ContextTypes.DEFAULT_TYPE):
    news = get_news()
    c.user_data['news'] = news
    btns = [[InlineKeyboardButton(f"{i+1}. {n['title'][:50]}...", callback_data=str(i))] for i, n in enumerate(news)]
    await u.message.reply_text("Выберите новость:", reply_markup=InlineKeyboardMarkup(btns))

async def click(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    if q.data == "pub":
        await c.bot.send_message(chat_id=CHANNEL, text=c.user_data['post'])
        await q.edit_message_text("🚀 Опубликовано!")
        return

    item = c.user_data['news'][int(q.data)]
    res = requests.post("https://routellm.abacus.ai/v1/chat/completions", 
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": f"Напиши пост для ТГ канала про: {item['title']}. Ссылка: {item['link']}. Стиль: лайфстайл, польза."}]})
    
    post = res.json()['choices'][0]['message']['content']
    c.user_data['post'] = post
    btn = [[InlineKeyboardButton("✅ Опубликовать", callback_data="pub")]]
    await q.edit_message_text(f"Превью:\n\n{post}", reply_markup=InlineKeyboardMarkup(btn))

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fetch", fetch))
    app.add_handler(CallbackQueryHandler(click))
    print("Запуск...")
    app.run_polling()
