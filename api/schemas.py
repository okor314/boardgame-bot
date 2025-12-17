from pydantic import BaseModel
from datetime import datetime
from typing import List

class Subscription(BaseModel):
    subscription_id: int
    user_id: int
    game_id: int
    created_at: datetime

class SubscriptionCreate(BaseModel):
    telegram_user_id: int
    game_id: int

    class Config:
        orm_mode = True

class SubsriptionOut(BaseModel):
    subscription_id: int
    game_id: int
    title: str

class Subscriptions(BaseModel):
    user_id: int
    subscriptions: List[SubsriptionOut]

class UserCreate(BaseModel):
    telegram_user_id: int

class User(BaseModel):
    id: int
    telegram_user_id: int
    created_at: datetime

    class Config:
        orm_mode = True
