from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, MetaData, Table
from api import models
from api import schemas
from api.database import engine, get_db
from api import utils

router = APIRouter(tags=["User"])

@router.post("/users", response_model=schemas.User, dependencies=[Depends(utils.require_key)])
def get_or_create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.execute(select(models.User.id, models.User.telegram_user_id, models.User.created_at)
                        .where(models.User.telegram_user_id == user.telegram_user_id)).mappings().first()

    if exists:
        return exists
    
    new_user = models.User(telegram_user_id=user.telegram_user_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user