import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from animal_facts import animals
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
WIKIPEDIA_BASE_URL = "https://ru.wikipedia.org"

def get_animal_info(animal_name):
    search_url = f"{WIKIPEDIA_BASE_URL}/w/index.php"
    params = {"search": animal_name, "title": "Special:Search", "go": "Go"}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        logger.error(f"Ошибка при запросе страницы: {response.status_code}")
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    summary_paragraphs = soup.find_all('p', limit=4)
    summary = ' '.join([p.get_text(strip=True) for p in summary_paragraphs])
    og_image_tag = soup.find('meta', property='og:image')
    image = og_image_tag['content'] if og_image_tag else None
    info = {
        "summary": summary,
        "url": response.url,
        "image": image,
        "title": soup.find('h1', id="firstHeading").get_text(strip=True)
    }
    return info

def get_animal_of_the_day():
    day_of_month = datetime.now().day - 1
    animal = animals[day_of_month]
    search_url = f"{WIKIPEDIA_BASE_URL}/w/index.php"
    params = {"search": animal['name'], "title": "Special:Search", "go": "Go"}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        logger.error(f"Ошибка при запросе страницы: {response.status_code}")
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    og_image_tag = soup.find('meta', property='og:image')
    image = og_image_tag['content'] if og_image_tag else None
    info = {
        "name": animal['name'],
        "fact": animal['fact'],
        "image": image,
        "url": response.url
    }
    return info

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Поиск по названию животного", callback_data='search_animal'),
            InlineKeyboardButton("Поиск по названию породы", callback_data='search_breed')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Я ЗооИнфо бот. Выберите, что вы хотите искать:',
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'search_animal':
        context.user_data['search_type'] = 'animal'
        await query.edit_message_text(text="Введите название животного:")
    elif query.data == 'search_breed':
        context.user_data['search_type'] = 'breed'
        await query.edit_message_text(text="Введите название породы:")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip().title()
    if context.user_data.get('search_type') in ['animal', 'breed']:
        info = get_animal_info(user_input)
        if info:
            response = f"**Название**: *{info['title']}*\n\n{info['summary']}\n\nЧитать больше: {info['url']}"
            if info['image']:
                await update.message.reply_photo(photo=info['image'])
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text('Извините, я не нашел информацию об этом животном.')

async def animal_of_the_day(update: Update, context: CallbackContext) -> None:
    info = get_animal_of_the_day()
    if info:
        response = f"**Животное дня**: *{info['name']}*\n\nИнтересный факт: {info['fact']}\n\nЧитать больше: {info['url']}"
        if info['image']:
            await update.message.reply_photo(photo=info['image'])
        await update.message.reply_text(response, parse_mode='Markdown')
    else:
        await update.message.reply_text('Извините, не удалось получить информацию о животном дня.')

def main() -> None:
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        logger.error("Токен бота не указан. Проверьте файл .env.")
        return
    try:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CommandHandler("animaloftheday", animal_of_the_day))
        application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()






