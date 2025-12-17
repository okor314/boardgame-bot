from sqlalchemy import Column, Integer, Boolean, Text, String, Date, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base

class User(Base):
    __tablename__ = 'bot_user'

    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(Integer, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class Subscription(Base):
    __tablename__ = 'subscription'

    subscription_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    game_id = Column(Integer, nullable=False)
    lastminprice = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    __table_args__ = (UniqueConstraint(user_id, game_id),)

class Game(Base):
    __tablename__ = 'game'

    id = Column(Integer, nullable=False, primary_key=True)
    title = Column(Text, nullable=False)
    gameland_id = Column(Integer)
    geekach_id = Column(Integer)
    woodcat_id = Column(Integer)

class Site(Base):
    __tablename__ = 'site'

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String(20), nullable=False)

class SiteTable(Base):
    __tablename__ = 'notexists'
    id = Column(Integer, nullable=False, primary_key=True)
    title = Column(Text, nullable=False)
    in_stock = Column(Boolean)
    price = Column(Integer)
    url = Column(Text, nullable=False)
    lastchecked = Column(Date, nullable=False)

class History(Base):
    __tablename__ = 'history'
    game_id = Column(Integer, nullable=False)
    site_id = Column(Integer, nullable=False)
    price = Column(Integer)
    checkdate = Column(Date, nullable=False)
    __table_args__ = (PrimaryKeyConstraint(game_id, site_id, checkdate),)