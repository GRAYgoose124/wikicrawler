import os

from .grabber import WikiGrabber
from .seeker import wikifetch
from .cacher import WikiCacher


class WikiCrawler:
    def traverse(self, url):
        path = []

        current_url = url
        with WikiCacher(os.getcwd() + '/data/databases/hopper.db') as wc:
            crawler = WikiGrabber(cacher=wc)


if __name__ == '__main__':
    crawler = WikiCrawler()
