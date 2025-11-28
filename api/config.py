from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='.env')

def config():
    db = {
        'host': os.getenv('DATABASE_HOST'),
        'port': os.getenv('DATABASE_PORT'),
        'database': os.getenv('DATABASE_DATABASE'),
        'user': os.getenv('DATABASE_USER'),
        'password': os.getenv('DATABASE_PASSWORD'),
    }

    return db