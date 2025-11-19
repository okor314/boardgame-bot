# boardgame-bot

## Description
**boardgame-bot** is a Telegram bot that helps users quickly find the **cheapest available price** for any board game across multiple online stores.

The bot connects to the **boardgame-aggregator** API and PostgreSQL database, where scraped data from supported e-commerce sites is stored.  
Users can search by game title, browse results, and instantly get links to the best offer.

---

## Technologies
- **Python 3.10+** — main bot logic  
- **python-telegram-bot v20+** — Telegram API wrapper  
- **FastAPI** — API backend for delivering boardgame data  
- **PostgreSQL** — data storage  
- **psycopg2** — database communications    
