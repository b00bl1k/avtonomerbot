from enum import IntEnum, auto

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, \
    String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from avbot.i18n import __

Base = declarative_base()


class Country(IntEnum):
    ru = auto()
    su = auto()
    us = auto()
    kz = auto()
    uz = auto()
    ge = auto()


COUNTRY_LABELS = {
    Country.ru.value: __("Russia"),
    Country.su.value: __("Soviet Union"),
    Country.us.value: __("United States"),
    Country.kz.value: __("Kazakhstan"),
    Country.uz.value: __("Uzbekistan"),
    Country.ge.value: __("Georgia"),
}


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    language_code = Column(String)
    country = Column(Integer)
    created_at = Column(DateTime)
    search_queries = relationship("SearchQuery")


class SearchQuery(Base):
    __tablename__ = "search_query"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    query_text = Column(String)
    num_type = Column(String(32), nullable=False)
    created_at = Column(DateTime)
    inline_queries = relationship("InlineQuery")


class InlineQuery(Base):
    __tablename__ = "inline_query"
    id = Column(Integer, primary_key=True)
    search_query_id = Column(Integer, ForeignKey("search_query.id"),
                             nullable=False)
    query = Column(String)
    created_at = Column(DateTime)
