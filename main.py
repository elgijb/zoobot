import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
import wikipediaapi

# Включение логирования для отладки и отслеживания ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Wikipedia API для получения данных с Википедии
wiki_wiki = wikipediaapi.Wikipedia('en')

def get_animal_info(animal_name):
    """
    Получает информацию о животном из Википедии.
    
    :param animal_name: Название животного для поиска.
    :return: Словарь с информацией о животном или None, если страница не найдена.
    """
    try:
        page = wiki_wiki.page(animal_name)
        if not page.exists():
            logger.info(f"Страница для '{animal_name}' не существует.")
            return None
        summary = page.summary.split('\n')[0]  # Извлекаем первый абзац из резюме
        images = page.images[:2]  # Получаем до 2 изображений
        info = {
            "summary": summary,
            "url": page.fullurl,
            "images": [f"https:{image}" for image in images if image.endswith(('jpg', 'jpeg', 'png'))],  # Форматируем URL
            "title": page.title
        }
        return info
    except wikipediaapi.WikipediaException as e:
        logger.error(f"Ошибка при получении информации о животном: {e}")
        return None

def get_habitat_info(habitat):
    """
    Получает список животных, обитающих в указанной среде, из Википедии.
    
    :param habitat: Название среды обитания для поиска.
    :return: Список словарей с информацией о найденных животных.
    """
    search_results = wiki_wiki.search(habitat, results=10)  # Поиск в Википедии
    animals = []
    for result in search_results:
        try:
            page = wiki_wiki.page(result)
            if not page.exists():
                continue  # Пропускаем, если страница не существует
            summary = page.summary.split('\n')[0]  # Извлекаем первый абзац из резюме
            images = page.images[:2]  # Получаем до 2 изображений
            animals.append({
                "title": result,
                "summary": summary,
                "url": page.fullurl,
                "images": [f"https:{image}" for image in images if image.endswith(('jpg', 'jpeg', 'png'))]  # Форматируем URL
            })
        except wikipediaapi.WikipediaException as e:
            logger.error(f"Ошибка при получении информации о среде обитания '{habitat}': {e}")
            continue  # Пропускаем, если произошла ошибка
    return animals

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
            media = [InputMediaPhoto(media=image) for image in info['images']]
            if media:
                await update.message.reply_media_group(media=media)  # Отправляем изображения
            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Извините, я не нашел информацию об этом животном. '
                                            'Возможно, вы допустили ошибку в написании названия или такой породы нет.')

    elif context.user_data.get('search_type') == 'habitat':
        animals = get_habitat_info(user_input)
        if animals:
            response = f'Животные, найденные в среде обитания "{user_input}":\n\n'
            for animal in animals:
                response += f"Название: {animal['title']}\n{animal['summary']}\n\nЧитать больше: {animal['url']}\n\n"
                media = [InputMediaPhoto(media=image) for image in animal['images']]
                if media:
                    await update.message.reply_media_group(media=media)  # Отправляем изображения
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f'Извините, я не нашел информацию о среде обитания "{user_input}". '
                                            'Возможно, вы допустили ошибку в написании или такой среды обитания нет.')

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











