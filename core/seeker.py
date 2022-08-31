import os
import re

import urllib.request
import urllib.parse
import bs4
from bs4 import BeautifulSoup as bs

from core.grabber import WikiGrabber
from core.db.cacher import WikiCacher

lang_code = "en"
base_url = f"https://{lang_code}.wikipedia.org"


class WikiSeeker(WikiGrabber):
    def __catlinks(self, page):
        categories = {}
        
        for link in page.find(id="catlinks", class_="catlinks").find_all('a'):
            categories[link['title']] = link['href']

        return categories

    def __disambiglinks(self, page):
        links = {}
        """This function assumes that it's being passed an identified disambiguation page."""
        for link in page.select('.mw-parser-output')[0].find_all('a'):
            try:
                if link['href'].startswith('/wiki/'):
                    links[link['title']] = link['href']
            except KeyError:
                pass

        return links

    def search(self, phrase):
        search_url = f"{base_url}/wiki/Special:Search?search={urllib.parse.quote(phrase, safe='')}&"

        # retrieve search page results - may be disambig, wikipage, or other?
        results = self.fetch(search_url)

        # handle disambiguation
        categories = self.__catlinks(results)
        if any(["Disambiguation" in cat for cat in categories]):
            options = list(self.__disambiglinks(results).values())
            results = options

        # retrieve actual results - using retrieve for caching.
        if isinstance(results, list):
            for result in results:
                yield self.retrieve(base_url + result, soup=True)
        else:
            yield self.retrieve(results.url, soup=True)

        return


if __name__ == '__main__':
    db_path = os.getcwd() + '/data/databases/seekerwiki.db'

    with WikiCacher(db_path) as wc:
        seeker = WikiSeeker(cacher=wc)

        for result in seeker.search(input("Wiki search: ")):
            print(result.url)
