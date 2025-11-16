import logging
import os
from dotenv import load_dotenv

import aiohttp
import asyncio

import io
import json
from thefuzz import fuzz, process

from telegram import (
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters,
)

load_dotenv(dotenv_path='./.env')
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
API_BASE_URL = 'http://127.0.0.1:8000'

SEARCH, REPORT = range(2)
TITLES = []
NUMBER_EMOJI = [f'{i}\uFE0F\u20E3' for i in range(11)]

async def apiGET(endpoint: str) -> dict:
    url = API_BASE_URL + endpoint
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json(encoding='utf-8')

async def getAllTitles():
    response = await apiGET('/titles')
    titles = [(game.get('id'), game.get('title')) for game in response]
    return titles

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



def match_buttons(matches: list[tuple[int, str]]) -> list:
    """Helper to create buttons with all matched games."""
    return [[InlineKeyboardButton(title, callback_data=str(id))] for id, title in matches]

def find_matches(query: str, choises: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Helper function to find games with title that contains
    words given in query."""
    words = query.lower().strip().split(' ')

    matches = filter(lambda x: any(word in x[1].lower() for word in words), choises)
    # Sorting by fuzz score of pair query-title
    matches = sorted(matches, key=lambda x: fuzz.WRatio(query, x[1]), reverse=True)
    return matches

def message_with_details(details: dict) -> str:
    """Helper function to create a massage about game details on each site."""
    meassage = ''
    sites = sorted(details.items(), key=lambda game: game[1].get('price'))
    for i, site in enumerate(sites, start=1):
        site_name = site[0]
        game_info = site[1]
        year, month, day = game_info['lastchecked'].split('-')

        # Use bold text for site name if game is in stock and cross out text if it is not
        name_tag = 'b' if game_info['in_stock'] in ['В наявності', 'Очікується'] else 's'
        meassage += (
            f'{NUMBER_EMOJI[i]} <{name_tag}>{site_name}</{name_tag}>\n'
            f'Ціна: <u>{int(game_info['price'])} грн.</u>\n'
            f'Статус: {game_info['in_stock']}\n'
            f'Назва: <a href=\"{game_info['url']}\">{game_info['title']}</a>\n'
            f'Остання перевірка: {day}.{month}\n\n'
        )

    meassage += ('Якщо ви помітили якусь помилку або неточність, '
                'можете повідомити про неї за допомогою команди /report')
    return meassage

async def prices_plot(history_details: dict):
    """Helper function to create   """
    datasets = [
        {
            "label": site_name,
            "fill": False,
            "data": [{"x": date, "y": price} for date, price in data.items()]
        }
        for site_name, data in history_details.items()
    ]

    request_params = {
        "type": "line",
        "data": {
            "datasets": datasets
        },
        "options": {
            "title": {
                "display": True,
                "text": "Історія цін"
            },
            "scales": {
            "xAxes": [{
                "type": "time",
                "ticks": {
                    "source": "data"
                },
                "time": {
                "parser": "YYYY-MM-DD",
                "displayFormats": {
                    "day": "DD-MM-YYYY"
                }
                }
            }]
            }
        }
        }
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://quickchart.io/chart", params={"c": json.dumps(request_params)}) as response:
            content = await response.read()
            img_bytes = io.BytesIO(content)
            img_bytes.seek(0)
            return img_bytes
            
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and explain how to search games."""
    global TITLES 
    TITLES = await getAllTitles()

    commands_keyboard = [['/start', '/report']]
    reply_markup = ReplyKeyboardMarkup(commands_keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Привіт! Щоб розпочати пошук ігор, введіть назву бажаної гри "\
        'або @shukachihorbot <назва гри> для пошуку з підказками.',
        reply_markup=reply_markup)

    return SEARCH

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: 
    """Search games similar to users query."""
    query = update.message.text
    matches = find_matches(query, TITLES)
 
    if not matches:
        matches = [choice[0] for choice in process.extractBests(query, TITLES)]
        keyboard = match_buttons(matches)
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Нічого не знайдено T_T\n' \
        'Можливо ви мали на увазі:', reply_markup=reply_markup)
        return SEARCH
    
    # If the first name is identical to the query, return the game data right away.
    if matches[0][1] == query:
        game_id = matches[0][0]
        game_detailes = await apiGET(f'/prices/{game_id}')

        message = message_with_details(game_detailes)
        history_button = [[InlineKeyboardButton("Подивитись історію цін", callback_data=f"show_history:{game_id}")]]
        reply_markup = InlineKeyboardMarkup(history_button)
        await update.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True, reply_markup=reply_markup)

        return SEARCH
    
    full_keyboard = match_buttons(matches)
    # if there a too many matches show olny three first
    if len(full_keyboard) > 3:
        short_keyboard = full_keyboard[:3]
        short_keyboard.append([InlineKeyboardButton('Показати ще', callback_data=f'show_more:{query}')])
    else:
        short_keyboard = full_keyboard
    
    reply_markup = InlineKeyboardMarkup(short_keyboard)
    await update.message.reply_text('Оберіть гру:', reply_markup=reply_markup)

    return SEARCH

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send user a message with details about the selected game."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('show_more:'):
        search_query = data.split(':')[1]
        matches = find_matches(search_query, TITLES)
        full_keyboard = match_buttons(matches)
        reply_markup = InlineKeyboardMarkup(full_keyboard)
        await query.edit_message_text('Оберіть гру:', reply_markup=reply_markup)
        return
    elif data.startswith('show_history:'):
        game_id = int(data.split(':')[1])
        history = await apiGET(f'/history/{game_id}')
        photo = await prices_plot(history)
        await query.message.reply_photo(photo)
        return
    
    game_id = int(data)
    game_detailes = await apiGET(f'/prices/{game_id}')

    message = message_with_details(game_detailes)
    history_button = [[InlineKeyboardButton("Подивитись історію цін", callback_data=f"show_history:{game_id}")]]
    reply_markup = InlineKeyboardMarkup(history_button)
    await query.message.reply_text(message, parse_mode='HTML', disable_web_page_preview=True, reply_markup=reply_markup)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Опишіть, будь ласка, проблему. Якщо помітили якусь неточність, '
                                    'вкажіть гру, якої вона стосується, або ваш пошуковий запит.\n\n'
                                    'Щоб просто повернутися до пошуку ігор, скористайтеся командою /cancel')
    return REPORT

async def handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send report message from user to admin"""
    text = update.message.text
    bot = update.get_bot()
    await bot.send_message(ADMIN_CHAT_ID, text)

    await update.message.reply_text("Дякую за вашу небайдужість! Можете продовжити пошук ігор.")
    return SEARCH

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels report entry"""
    await update.message.reply_text(
        "Ви повернулися в режим пошуку. Щоб знайти бажану гру, введіть її назву або @shukachihorbot <назва гри>."
    )

    return SEARCH

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the inline query. This is run when you type: @botusername <query>"""
    chat_type = update.inline_query.chat_type
    query = update.inline_query.query
    if not query:  # empty query should not be handled
        global TITLES 
        TITLES = await getAllTitles()
        return
    
    matches = find_matches(query, TITLES)
    if not matches:
        matches = [choice[0] for choice in process.extractBests(query, TITLES)]
    # Limit 50 results per query
    matches = matches[:50]

    if chat_type == 'sender':
        results = [
            InlineQueryResultArticle(
                id=str(id),
                title=title,
                input_message_content=InputTextMessageContent(title)
            )
            for id, title in matches
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id=str(id),
                title=title,
                input_message_content=InputTextMessageContent(title),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Деталі', callback_data=f'detail_data:{id}')]])
            )
            for id, title in matches
        ]

    await update.inline_query.answer(results)

async def detail_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handeler for button Деталі for inline search result in private or group chats"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith('detail_data:'):
        game_id = int(data.split(':')[1])
        game_detailes = await apiGET(f'/prices/{game_id}')

        message = message_with_details(game_detailes)
        await query.edit_message_text(message, parse_mode='HTML', disable_web_page_preview=True)


async def error_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends error message when user respond with message or command
    that cannot be handled."""
    await update.message.reply_text('Йой, мені не вдалося зрозуміти, що це. '\
                                    'Спробуйте написати іншу назву гри або скористатися доступними команами:\n\n'\
                                    '/start - почати пошук ігор.\n'\
                                    '/report - повідомити про проблему.')
    
    



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("report", report)],
        states={
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback=search),
                     CallbackQueryHandler(button),
                     CommandHandler('report', report)],
            REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback=handle_report),
                     CommandHandler('cancel', cancel)]
        },
        fallbacks=[MessageHandler(filters=None, callback=error_message)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(detail_button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()