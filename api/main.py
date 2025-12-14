from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from api import models
from api.routers import price, subscription
from api.database import engine, get_db

app = FastAPI()

@app.get("/titles")
def get_titles(db: Session = Depends(get_db)):
    stmt = (
        select(models.Game.id, models.Game.title)
        .order_by(models.Game.id)
    )

    rows = db.execute(stmt).mappings().all()
    return rows

@app.get("/titles/{id}")
def get_title(id: int, db: Session = Depends(get_db)):
    stmt = (
        select(models.Game.id, models.Game.title)
        .where(models.Game.id == id)
    )

    row = db.execute(stmt).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не вдалося знайти гру"
        )

    return row


app.include_router(price.router)
app.include_router(subscription.router)
