import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv('./test.env')

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("BOT_API_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def require_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")