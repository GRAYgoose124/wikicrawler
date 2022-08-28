import os

from database import DBMan, DBPageEntry, Column, Text, JSON, Base
from sqlalchemy.exc import NoResultFound


class PageCacher:
    def __init__(self, db_path):
        self.manager = None
        self.db_path = db_path

        if not os.path.exists(db_path):
            os.makedirs(db_path)

    def __enter__(self):
        # Dummy implementation, see db.py for more info. 
        self.manager = DBMan(self.db_path, DBPageEntry)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.close()
        self.manager = None

    def __contains__(self, url):
        try:
            self.manager.session.query(self.manager.Node).filter(self.manager.Node.url == url).one()
            return True
        except NoResultFound:
            return False

    def cache(self, page): 
        if self.manager is not None: 
            self.manager.session.merge(self.manager.Node(**page))


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
        self.manager = DBMan(self.db_path, DBWikiPageEntry)
        return self
