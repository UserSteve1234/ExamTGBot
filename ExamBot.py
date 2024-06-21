import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from env import KEY, EDAMAM_KEY, EDAMAM_ID

TELEGRAM_TOKEN = KEY
EDAMAM_APP_ID = EDAMAM_ID
EDAMAM_APP_KEY = EDAMAM_KEY
APERTIUM_API_URL = "https://apy.projectjj.com/translate"  # URL Apertium API

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ENTER_RECIPE_NAME = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я бот для поиска рецептов. Нажми /main, чтобы начать.')

async def main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Найти рецепт", callback_data='find_recipe')],
        [InlineKeyboardButton("Отмена", callback_data='cancel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'find_recipe':
        await query.message.reply_text('Введите название блюда, чтобы найти рецепт:')
        return ENTER_RECIPE_NAME
    elif query.data == 'cancel':
        await query.message.reply_text('Отменено.')
        return ConversationHandler.END

def translate_text_apertium(text: str, source_language: str = "en", target_language: str = "ru") -> str:
    try:
        response = requests.get(APERTIUM_API_URL, params={
            "langpair": f"{source_language}|{target_language}",
            "q": text
        }, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if 'responseData' in data and 'translatedText' in data['responseData']:
            translated_text = data['responseData']['translatedText']
            logging.info(f"Translated '{text}' to '{translated_text}'")
            return translated_text
        else:
            logging.warning(f"Unexpected response format from Apertium API: {data}")
            return text
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error requesting translation from Apertium API: {e}")
        return text
    
    except Exception as e:
        logging.error(f"Unexpected error during translation: {e}")
        return text

async def enter_recipe_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dish_name = update.message.text
    
    url = f'https://api.edamam.com/search?q={dish_name}&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}'
    logging.info(f"Requesting recipes for dish: {dish_name}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logging.info(f"Received data: {data}")
        
        if 'hits' in data and len(data['hits']) > 0:
            recipe_data = data['hits'][0]['recipe']
            recipe_name = recipe_data['label']
            recipe_url = recipe_data['url']
            recipe_image = recipe_data['image']
            ingredients = recipe_data['ingredientLines']
            logging.info(f"Original ingredients: {ingredients}")
            
            translated_ingredients = [translate_text_apertium(ingredient) for ingredient in ingredients]
            ingredients_text = "\n".join(f"- {ingredient}" for ingredient in translated_ingredients)
            logging.info(f"Translated ingredients: {ingredients_text}")
            
            message_text = f'Рецепт: {recipe_name}\n{recipe_url}\n\nИнгредиенты:\n{ingredients_text}'
            await context.bot.send_photo(chat_id=update.message.chat_id, photo=recipe_image, caption=message_text)
        else:
            await update.message.reply_text('К сожалению, не удалось найти рецепт для этого блюда.')
    
    except requests.exceptions.RequestException as e:
        logging.error(f'Ошибка при запросе к Edamam API: {e}')
        await update.message.reply_text('Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.')
    
    except Exception as e:
        logging.error(f'Неожиданная ошибка: {e}')
        await update.message.reply_text('Произошла неожиданная ошибка. Пожалуйста, попробуйте снова позже.')
    
    return ConversationHandler.END

def main_function() -> None:
    start_handler = CommandHandler('start', start)
    main_handler = CommandHandler('main', main)
    button_handler = CallbackQueryHandler(button)
    enter_recipe_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, enter_recipe_name)
    
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(start_handler)
    application.add_handler(main_handler)
    application.add_handler(button_handler)
    application.add_handler(enter_recipe_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main_function()
