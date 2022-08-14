import os
import sqlalchemy as sa
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Text
from sqlalchemy.sql.expression import func
import re

dir_path = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(dir_path, 'wiki.db')
if os.name == 'nt':
    db_path = f'sqlite:///{db_path}'
else:
    db_path = f'sqlite:////{db_path}'


# create  regex function for sqlite and import it
@sa.event.listens_for(sa.engine.Engine, 'connect')
def sqlite_engine_connect(dbapi_conn, connection_record):
    dbapi_conn.create_function('regexp', 2, _regexp)


def _regexp(expr, item):
    if item is None:
        return
    reg = re.compile(expr, re.I)
    return reg.search(item) is not None  #


# init db
Base = declarative_base()


class Node(Base):
    __tablename__ = 'facts'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    wiki_page = Column(Text, nullable=False)


engine = create_engine(db_path)
Node.metadata.create_all(engine)
Base.metadata.bind = engine


def create_session():
    global engine
    DBsession = sessionmaker(bind=engine)
    return DBsession()


class DBMan():
    def __init__(self):
        self.session = create_session()

    def __del__(self):
        self.session.commit()
        self.session.close()
    
