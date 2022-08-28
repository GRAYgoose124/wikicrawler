import os

from grabber import WikiGrabber
from cacher import WikiCacher
from parasentiment import analyze_page, parse_page


class WikiCrawler:
    def traverse(self, url):
        path = []

        current_url = url
        with WikiCacher(os.getcwd() + '/databases/hopper.db') as wc:
            crawler = WikiGrabber(cacher=wc)


if __name__ == '__main__':
    hopper = WikiCrawler()
