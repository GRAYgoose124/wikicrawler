import os
import re
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Text, JSON
from sqlalchemy.sql.expression import func


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


# Default entry
class DBPageEntry(Base):
    __tablename__ = 'pages'
    url = Column(Text, nullable=False, primary_key=True)


class DBMan():
    def __init__(self, node, db_name, db_path=None):  
        if db_path is None:
            db_path = os.getcwd() + '/databases'      
        db_full_path = db_path + '/' + db_name
        
        if os.name == 'nt':
            db_full_path = f'sqlite:///{db_full_path}'
        else:
            db_full_path = f'sqlite:////{db_full_path}'

        self.db_path = db_full_path

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

