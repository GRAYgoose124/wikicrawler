import os

from core.seeker import WikiSeeker
from core.db.cacher import WikiCacher


class WikiCrawler(WikiSeeker):
    def traverse(self, url):
        path = []


if __name__ == '__main__':
    with WikiCacher(os.getcwd() + '/data/databases/crawler.db') as wc:
        crawler = WikiCrawler(cacher=wc)
