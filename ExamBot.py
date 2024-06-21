from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ApplicationBuilder,
    ContextTypes,
)
import logging
import requests
# from env import KEY, EDAMAM_KEY, EDAMAM_ID

TELEGRAM_TOKEN = KEY
EDAMAM_APP_ID = EDAMAM_ID
EDAMAM_APP_KEY = EDAMAM_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levellevelname)s - %(message)s',
    level=logging.INFO
)

ENTER_RECIPE_NAME = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am a recipe search bot. Press /main to start.')

async def main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("Find a recipe"), KeyboardButton("Cancel")],
        [KeyboardButton("About this bot")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text('Select an action:', reply_markup=reply_markup)

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    
    if text == 'Find a recipe':
        await update.message.reply_text('Enter the name of the dish to find a recipe:')
        return ENTER_RECIPE_NAME
    elif text == 'Cancel':
        await update.message.reply_text('Cancelled.')
        return ConversationHandler.END
    elif text == 'About this bot':
        await update.message.reply_text('This bot was created by Muminov Sardor.')
    

async def enter_recipe_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    dish_name = update.message.text
    
    url = f'https://api.edamam.com/search?q={dish_name}&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if 'hits' in data and len(data['hits']) > 0:
            recipe_data = data['hits'][0]['recipe']
            recipe_name = recipe_data['label']
            recipe_url = recipe_data['url']
            recipe_image = recipe_data['image']
            ingredients = recipe_data['ingredientLines']
            
            ingredients_text = "\n".join(f"- {ingredient}" for ingredient in ingredients)
            message_text = f'Recipe: {recipe_name}\n{recipe_url}\n\nIngredients:\n{ingredients_text}'
            await context.bot.send_photo(chat_id=update.message.chat_id, photo=recipe_image, caption=message_text)
        else:
            await update.message.reply_text('Unfortunately, no recipe could be found for this dish.')
    
    except Exception as e:
        logging.error(f'Error requesting Edamam API: {e}')
        await update.message.reply_text('An error occurred while processing your request.')
    
    return ConversationHandler.END

def main_function() -> None:
    start_handler = CommandHandler('start', start)
    main_handler = CommandHandler('main', main)
    menu_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)
    enter_recipe_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, enter_recipe_name)
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(start_handler)
    app.add_handler(main_handler)
    app.add_handler(menu_handler)
    app.add_handler(enter_recipe_handler)
    
    app.run_polling()

if __name__ == '__main__':
    main_function()
