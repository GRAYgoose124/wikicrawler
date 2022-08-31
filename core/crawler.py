import os

from core.seeker import WikiSeeker
from core.db.cacher import WikiCacher


class WikiCrawler(WikiSeeker):
    def traverse(self, url):
        path = []


if __name__ == '__main__':
    crawler = WikiCrawler()
