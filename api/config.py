from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='test.env')

def config(return_url=False):
    db = {
        'host': os.getenv('DATABASE_HOST'),
        'port': os.getenv('DATABASE_PORT'),
        'database': os.getenv('DATABASE_DATABASE'),
        'user': os.getenv('DATABASE_USER'),
        'password': os.getenv('DATABASE_PASSWORD'),
    }

    if return_url:
        db = f'postgresql://{db['user']}:{db['password']}@{db["host"]}:{db["port"]}/{db["database"]}'

    return db