import os

from .database import DBMan, DBPageEntry, Column, Text, JSON, Base
from sqlalchemy.exc import NoResultFound


class PageCacher:
    """ The PageCacher is a context manager that manages the database connection automatically.

    This class provides the ability to cache pages into a database, and retrieve them transparently.

    It can be extended to use other databases, or other caching methods. TODO: csv/json backends.
    """
    def __init__(self, config, parent_logger=None):
        self.logger = parent_logger.getChild(__name__) if parent_logger is not None else logging.getLogger(__name__)
        
        self.config = config
        self._manager = None
        self.hooks = []

        self.db_path = config['data_root'] + f"/databases/{config['db_file']}"

        if not os.path.exists(config['data_root'] + "/databases"):
            os.makedirs(config['data_root'] + "/databases")

    @property
    def manager(self):
        return self._manager

    def __enter__(self):
        return self.start()
    
    def start(self):
        # Dummy implementation, see db.py for more info. 
        if self.manager is None:
            self._manager = DBMan(DBPageEntry, self.db_path)
        
        return self

    def close(self):
        self.manager.close()
        self._manager = None

        # note: for unifying/ensuring/syncronizing all save operations.
        for hook in self.hooks:
            hook()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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
    """ This class is a database entry for a wikipeida page. It is used by the WikiCacher to store pages in it's specialized database.
    """
    title = Column(Text, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    paragraph_links = Column(JSON, nullable=True)
    toc_links = Column(JSON, nullable=False) # TODO: rename to toc_links
    see_also = Column(JSON, nullable=True)
    references = Column(JSON, nullable=False)
    media = Column(JSON, nullable=True)


class WikiCacher(PageCacher):
    """ The WikiCacher is a specialized PageCacher that caches wikipedia pages only.
    """
    def start(self):
        self._manager = DBMan(DBWikiPageEntry, self.db_path)
        return self
