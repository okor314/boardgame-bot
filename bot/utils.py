import aiohttp
from telegram import InlineKeyboardButton
from thefuzz import fuzz, process

import io
import json

NUMBER_EMOJI = [f'{i}\uFE0F\u20E3' for i in range(11)]

def match_buttons(matches: list[tuple[int, str]]) -> list:
    """Helper to create buttons with all matched games."""
    return [[InlineKeyboardButton(title, callback_data=str(id))] for id, title in matches]

def find_matches(query: str, choises: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Helper function to find games with title that contains
    words given in query."""
    words = query.lower().strip().split(' ')

    matches = filter(lambda x: any(word in x[1].lower() for word in words if x[1]), choises)
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
        name_tag = 'b' if game_info['in_stock'] else 's'
        meassage += (
            f'{NUMBER_EMOJI[i]} <{name_tag}>{site_name}</{name_tag}>\n'
            f'Ціна: <u>{int(game_info['price'])} грн.</u>\n'
            f'Статус: {['Немає в наявності', 'В наявності'][game_info['in_stock']]}\n'
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