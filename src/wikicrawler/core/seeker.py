import os
import re

from functools import partial
import urllib.request
import urllib.parse
import bs4
from bs4 import BeautifulSoup as bs

from .grabber import WikiGrabber
from .db.cacher import WikiCacher


lang_code = "en"
base_url = f"https://{lang_code}.wikipedia.org"


class WikiSeeker(WikiGrabber):
    def __catlinks(self, page):
        """ Finds the categories of a general page.
        
        This function returns a list of categories that the page belongs to. 
        """
        categories = {}

        try:        
            for link in page.find(id="catlinks", class_="catlinks").find_all('a'):
                categories[link['title']] = link['href']
        except AttributeError:
            pass

        return categories

    def __disambiglinks(self, page):
        links = {}
        """This function assumes that it's being passed an identified disambiguation page.
        
        It returns a dictionary of links to the disambiguation results.
        """
        for link in page.select('.mw-parser-output')[0].find_all('a'):
            try:
                if link['href'].startswith('/wiki/'):
                    links[link['title']] = link['href']
            except KeyError:
                pass

        return links

    def __speciallinks(self, page):
        """ This function assumes that it's being passed a special search page. 
        
        It returns a dictionary of links to the search results.
        """
        links = {}

        try:
            page = page.select(".mw-search-results")[0]
        except IndexError:
            pass
    
        for link in page.find_all('a'):
            try:
                if link['href'].startswith('/wiki/'):
                    links[link['title']] = link['href']
            except KeyError:
                pass

        return links

    def search(self, phrase, precache=False):
        """
        Searches wikipedia for a phrase and yields a generator of results.

        Args: 
            phrase (str): The phrase to search for.
            precache (bool): Whether or not to precache the results. (Very slow. TODO: Async fix)

        Returns:
            generator: A generator of result pairs, which are a tuple of the title and the retrieved page,
                        or a partial function to retrieve the page at a later date if precache is False.
        """
        search_url = f"{base_url}/wiki/Special:Search?search={urllib.parse.quote(phrase, safe='')}&"

        # retrieve search page results - may be disambig, wikipage, or other?
        results = self.fetch(search_url)
        if results is None:
            return (None, None)
            
        # handle special search
        if results.url.startswith(f"{base_url}/wiki/Special:Search?"):
            for result in self.__speciallinks(results).values():
                if not precache:
                    yield (result, partial(self.retrieve, base_url + result))
                else:
                    yield (result, self.retrieve(base_url + result))

        # handle disambiguation
        categories = self.__catlinks(results)
        if any(["Disambiguation" in cat for cat in categories]):
            for result in self.__disambiglinks(results).values():
                if not precache:
                    yield (result, partial(self.retrieve, base_url + result))
                else:
                    yield (result, self.retrieve(base_url + result))
        else:
            yield (None, self.retrieve(results.url, page=results))


if __name__ == '__main__':
    db_path = os.getcwd() + '/data/databases/seekerwiki.db'

    with WikiCacher(db_path) as wc:
        seeker = WikiSeeker(cacher=wc)

        for result in seeker.search("Star"):
            print(result['url'])
