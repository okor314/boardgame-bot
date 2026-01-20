from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, MetaData, Table
from api import models
from api import schemas
from api.database import engine, get_db
from api import utils



router = APIRouter(tags=["Subscriptions"])


@router.get('/subscriptions/user/{user_id}', response_model=schemas.Subscriptions, dependencies=[Depends(utils.require_key)])
def get_subs(user_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(models.Subscription.game_id, models.Game.title, models.Subscription.created_at)
        .select_from(models.Subscription)
        .join(models.Game, models.Subscription.game_id == models.Game.id)
        .where(models.Subscription.user_id == user_id)
    )

    subs = db.execute(stmt).mappings().all()

    return {'user_id': user_id, 'subscriptions': subs}

@router.get("/subscriptions/by-telegram/{telegram_user_id}",
            response_model=schemas.Subscriptions, dependencies=[Depends(utils.require_key)])
def get_subs(telegram_user_id: int, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.telegram_user_id == telegram_user_id).first()
    if not user:
        return {"user_id": None, "subscriptions": []}
    
    stmt = (
        select(models.Subscription.game_id, models.Game.title, models.Subscription.created_at)
        .select_from(models.Subscription)
        .join(models.Game, models.Subscription.game_id == models.Game.id)
        .where(models.Subscription.user_id == user.id)
        .order_by(models.Subscription.created_at.desc())
    )

    subs = db.execute(stmt).mappings().all()

    return {'user_id': user.id, 'subscriptions': subs}

@router.post('/subscriptions', status_code=status.HTTP_201_CREATED, response_model=schemas.Subscription, dependencies=[Depends(utils.require_key)])
def create_sub(subscription: schemas.SubscriptionCreate, db: Session = Depends(get_db)):
    # Check if user exists
    user_id = db.execute(select(models.User.id).where(models.User.telegram_user_id == subscription.telegram_user_id)).first()
    if not user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Не вдалося знайти користувача')
    user_id = user_id[0]

    # Check if subscription already exists
    exists = db.execute(
        select(models.Subscription.user_id)
        .where(models.Subscription.user_id == user_id) 
        .where(models.Subscription.game_id == subscription.game_id)
              ).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, 'Subscription already exists')
    
    # Check if game exists
    game = db.get(models.Game, subscription.game_id)
    if not game:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Не вдалося знайти гру')
    
    # Limit number of subscriptions per user
    subs = db.query(models.Subscription).filter(models.Subscription.user_id == user_id).all()
    if len(subs) == 10:
        raise HTTPException(status.HTTP_403_FORBIDDEN, 
                            'Forbidden: reached limit of subscriptions per user')
    # Extract min price
    sites = db.execute(select(models.Site.name)).mappings().all()
    prices = {}
    metadata = MetaData() 
    for site in sites:
        table_id = getattr(game, f'{site['name']}_id')
        if not table_id: continue

        site_table = Table(site['name'], metadata, autoload_with=db.get_bind())
        stmt = (
            select(site_table.c.price)
            .where(site_table.c.id == table_id)
        )
        table_game = db.execute(stmt).mappings().first()
        if table_game['price'] is not None:
            prices[site['name']] = table_game['price']

    # Add subcription to dataabse
    new_sub = models.Subscription(user_id=user_id, game_id=subscription.game_id, lastminprice = min(prices.values()))
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)


    return new_sub

@router.delete('/subscriptions/{id}', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(utils.require_key)])
def delete_sub(id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscription).filter(models.Subscription.subscription_id == id)
    
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Не вдалося знайти підписку з id: {id}")

    sub.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete('/subscriptions', status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(utils.require_key)])
def delete_sub(payload: schemas.SubscriptionDelete, db: Session = Depends(get_db)):
    sub = (db.query(models.Subscription)
           .select_from(models.Subscription)
           .join(models.User, models.Subscription.user_id == models.User.id)
           .filter(models.User.telegram_user_id == payload.telegram_user_id,
                   models.Subscription.game_id == payload.game_id)
            .first())

    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Не вдалося знайти підписку")

    db.delete(sub)
    db.commit()

    return {'status_code': 204}

@router.get('/subscriptions/status')
def isSubscribed(telegram_user_id: int, game_id: int, db: Session = Depends(get_db)):
    user_id = db.execute(
        select(models.User.id)
        .where(models.User.telegram_user_id == telegram_user_id)).first()
    if not user_id:
        return {"status": False}

    sub = db.execute(
        select(models.Subscription.subscription_id)
        .where((models.Subscription.user_id == user_id[0]) & 
               (models.Subscription.game_id == game_id))
               ).first()
    
    return {"status": bool(sub)}