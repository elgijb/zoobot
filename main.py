import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from bs4 import BeautifulSoup

# Включение логирования для отладки и отслеживания ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WIKIPEDIA_BASE_URL = "https://ru.wikipedia.org"

def get_animal_info(animal_name):
    """
    Получает основную информацию и одно изображение о животном из Википедии.
    
    :param animal_name: Название животного для поиска.
    :return: Словарь с информацией о животном и изображением или None, если страница не найдена.
    """
    try:
        search_url = f"{WIKIPEDIA_BASE_URL}/w/index.php"
        params = {"search": animal_name, "title": "Special:Search", "go": "Go"}
        response = requests.get(search_url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Ошибка при запросе страницы: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Получение основного контента из contentSub
        content_sub = soup.find('div', id='contentSub')
        summary = content_sub.get_text(strip=True) if content_sub else "Описание не найдено."

        # Получение первого изображения из og:image
        og_image_tag = soup.find('meta', property='og:image')
        image = og_image_tag['content'] if og_image_tag else None

        # Получение заголовка страницы
        title = soup.find('h1', id="firstHeading").get_text(strip=True)

        info = {
            "summary": summary,
            "url": response.url,
            "image": image,
            "title": title
        }
        return info
    except Exception as e:
        logger.error(f"Ошибка при получении информации о животном: {e}")
        return None

async def start(update: Update, context: CallbackContext) -> None:
    """
    Обработчик команды /start, отображает клавиатуру с опциями.
    
    :param update: Обновление, содержащее информацию о сообщении.
    :param context: Контекст, содержащий данные о команде.
    """
    keyboard = [
        [
            InlineKeyboardButton("Поиск по названию животного", callback_data='search_animal'),
            InlineKeyboardButton("Поиск по названию породы", callback_data='search_breed')
        ],
        [InlineKeyboardButton("Поиск по среде обитания", callback_data='search_habitat')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Привет! Я ЗооИнфо бот. Выберите, что вы хотите искать:',
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    """
    Обработчик нажатий на кнопки в инлайн-клавиатуре.
    
    :param update: Обновление, содержащее информацию о нажатой кнопке.
    :param context: Контекст, содержащий данные о нажатии.
    """
    query = update.callback_query
    await query.answer()  # Подтверждение получения запроса

    # Определение типа поиска на основе нажатой кнопки
    if query.data == 'search_animal':
        context.user_data['search_type'] = 'animal'
        await query.edit_message_text(text="Введите название животного:")
    elif query.data == 'search_breed':
        context.user_data['search_type'] = 'breed'
        await query.edit_message_text(text="Введите название породы:")
    elif query.data == 'search_habitat':
        context.user_data['search_type'] = 'habitat'
        await query.edit_message_text(text="Введите название среды обитания:")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """
    Обработчик текстовых сообщений, осуществляет поиск по введенному запросу.
    
    :param update: Обновление, содержащее информацию о сообщении.
    :param context: Контекст, содержащий данные о сообщении.
    """
    user_input = update.message.text.strip().title()

    if context.user_data.get('search_type') in ['animal', 'breed']:
        info = get_animal_info(user_input)
        if info:
            response = f"Название: {info['title']}\n\n{info['summary']}\n\nЧитать больше: {info['url']}"
            if info['image']:
                media = InputMediaPhoto(media=info['image'])
                await update.message.reply_photo(photo=media.media)  # Отправляем одно изображение
            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Извините, я не нашел информацию об этом животном. '
                                            'Возможно, вы допустили ошибку в написании названия или такой породы нет.')

def main() -> None:
    """
    Основная функция для запуска бота.
    """
    # Вставьте сюда токен вашего бота
    TOKEN = '7310780555:AAFwdne8UHZEWPBobQM7ER830ymW3J0gv2g'

    if not TOKEN:
        logger.error("Токен бота не указан. Проверьте переменную TOKEN.")
        return

    try:
        # Создание и настройка бота с отключенными обработчиками сигналов
        application = Application.builder().token(TOKEN).build()

        # Добавление обработчиков команд и сообщений
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Запуск бота
        application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()


