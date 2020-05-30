from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

import models
import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()


def get_one_or_create(model, create_method="", create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), False
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        created = getattr(model, create_method, model)(**kwargs)
        try:
            session.add(created)
            session.flush()
            return created, True
        except IntegrityError:
            session.rollback()
            return session.query(model).filter_by(**kwargs).one(), False


def get_or_create_user(telegram_id, first_name, last_name, username,
                       language_code):
    user, _ = get_one_or_create(
        models.User,
        create_method_kwargs={
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "created_at": datetime.utcnow(),
            "language_code": language_code,
        },
        telegram_id=telegram_id,
    )
    return user


def add_search_query(user, query_text):
    search_query = models.SearchQuery(
        query_text=query_text,
        created_at=datetime.utcnow(),
    )
    user.search_queries.append(search_query)
    session.commit()
    return search_query


def get_search_query(search_query_id):
    return session.query(models.SearchQuery).get(search_query_id)


def add_inline_query(search_query, query):
    inline_query = models.InlineQuery(
        query=query,
        created_at=datetime.utcnow(),
    )
    search_query.inline_queries.append(inline_query)
    session.commit()
    return inline_query
