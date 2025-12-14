from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, Table, MetaData
from api import models
from api.database import engine, get_db


router = APIRouter()

@router.get("/prices/{id}")
def get_prices(id: int, db: Session = Depends(get_db)):
    stmt = (
        select(models.Site.id, models.Site.name)
    )
    sites = db.execute(stmt).mappings().all()

    game = db.get(models.Game, id)
    if not game:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Не вдалося знайти гру')

    result = {}
    metadata = MetaData() 
    for site in sites:
        table_id = getattr(game, f'{site['name']}_id')
        if not table_id: continue

        site_table = Table(site['name'], metadata, autoload_with=db.get_bind())
        stmt = (
            select(site_table.c.id, 
                   site_table.c.title, 
                   site_table.c.in_stock, 
                   site_table.c.price, 
                   site_table.c.url,
                   site_table.c.lastchecked)
            .where(site_table.c.id == table_id)
        )
        table_game = db.execute(stmt).mappings().first()
        
        result[site['name']] = table_game

    return result

@router.get('/prices/{id}/history')
def get_history(id: int, db: Session = Depends(get_db)):
    stmt = (
        select(models.Site.name, models.History.price, models.History.checkdate)
        .select_from(models.History)
        .join(models.Site, models.History.site_id == models.Site.id)
        .where(models.History.game_id == id)
        .order_by(models.History.checkdate)
    )

    rows = db.execute(stmt).mappings().all()
    
    result = {}
    for row in rows:
        site_name = row['name']
        price = row['price']
        date = row['checkdate']

        if result.get(site_name) is None:
            result[site_name] = {date: price}
        else:
            result[site_name].update({date: price})
            
    return result
