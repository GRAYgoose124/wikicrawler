import os

from .database import DBMan, DBPageEntry, Column, Text, JSON, Base
from sqlalchemy.exc import NoResultFound


class PageCacher:
    def __init__(self, db_path):
        self.manager = None
        self.hooks = []

        if db_path is not None:
            self.db_path, self.db_name = db_path.rsplit('/', 1)
        else:
            self.db_path, self.db_name = os.getcwd() + '/data/databases', 'database.db'

        # splitting to remove db name from path
        db_root = db_path.rsplit(os.path.sep, 1)[0]
        if not os.path.exists(db_root):
            os.makedirs(db_root)

    def __enter__(self):
        # Dummy implementation, see db.py for more info. 
        self.manager = DBMan(DBPageEntry, self.db_name, self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.close()
        self.manager = None

        for hook in self.hooks:
            hook()

    def __contains__(self, url):
        try:
            self.manager.session.query(self.manager.Node).filter(self.manager.Node.url == url).one()
            return True
        except NoResultFound:
            return False

    def get(self, key):
        return self.manager.session.query(self.manager.Node).filter(self.manager.Node.url == key).one()


    def cache(self, page): 
        if self.manager is not None: 
            self.manager.session.merge(self.manager.Node(**page))

    def register_hook(self, hook):
        self.hooks.append(hook)


class DBWikiPageEntry(DBPageEntry, Base):
    title = Column(Text, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    paragraph_links = Column(JSON, nullable=True)
    toc_links = Column(JSON, nullable=False) # TODO: rename to toc_links
    see_also = Column(JSON, nullable=True)
    references = Column(JSON, nullable=False)
    media = Column(JSON, nullable=True)


class WikiCacher(PageCacher):
    def __enter__(self):
        self.manager = DBMan(DBWikiPageEntry, self.db_name, self.db_path)
        return self
