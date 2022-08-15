import os
import sqlalchemy as sa
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Text, JSON
from sqlalchemy.sql.expression import func
import re


# create  regex function for sqlite and import it
@sa.event.listens_for(sa.engine.Engine, 'connect')
def sqlite_engine_connect(dbapi_conn, connection_record):
    dbapi_conn.create_function('regexp', 2, _regexp)


def _regexp(expr, item):
    if item is None:
        return
    reg = re.compile(expr, re.I)
    return reg.search(item) is not None  #


Base = declarative_base()


class DBMan():
    def __init__(self, db_name, node):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # TODO: Need to mkdir databases.
        db_path = os.path.join(dir_path, 'databases', db_name)

        if os.name == 'nt':
            db_path = f'sqlite:///{db_path}'
        else:
            db_path = f'sqlite:////{db_path}'

        self.db_path = db_path

        self.Base = Base
        self.Node = node
      
        self.session = self.create_session()

    def __del__(self):
        self.close()

    def close(self):
        self.session.commit()
        self.session.close()
    
    def create_session(self):
        engine = create_engine(self.db_path)

        self.Node.metadata.create_all(engine)
        self.Base.metadata.bind = engine

        DBsession = sessionmaker(bind=engine)

        return DBsession()

