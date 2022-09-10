import os

from .seeker import WikiSeeker
from .db.cacher import WikiCacher


class WikiCrawler(WikiSeeker):
    def traverse(self, start_page, tags):
        path = []
        
        # href traversal


if __name__ == '__main__':
    with WikiCacher(os.getcwd() + '/data/databases/crawler.db') as wc:
        crawler = WikiCrawler(cacher=wc)
