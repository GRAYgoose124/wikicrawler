from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from multiprocessing import Pool
import os
import json
import time

import urllib
from urllib import response
import urllib.request
import urllib.parse
import logging
import bs4
from bs4 import BeautifulSoup as bs
from pathlib import Path
from time import sleep

import re 
import threading

from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text

from .db.cacher import WikiCacher
from .utils.model_to_dict import model_to_dict


def media_retrieve_wrapper(dl_url, save_loc):
    try:
        urllib.request.urlretrieve(dl_url, save_loc)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        # logger.debug("Failed to download media. - Likely rate limited.")
        sleep(5)
        media_retrieve_wrapper(dl_url, save_loc)


# TODO: make grabber asyncronous
class WikiGrabber:
    """ WikiGrabber is a class that handles the fetching of wikipedia pages

    It is used to fetch pages from wikipedia and parse them into a format
    that can be used by the arbiter and seer. It uses the cacher to store
    the pages it fetches so that it can store pages transparently.
    """
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*\..*")
    header_regex = re.compile('^h[1-6]$')

    def __init__(self, config, cacher=None, parent_logger=None):
        """ Initializes the WikiGrabber class.

        Args:
            config (dict): The configuration dictionary. 
            cacher (WikiCacher): The cacher to use. If none is provided, no caching is performed.
        """
        self.logger = parent_logger.getChild(__name__)
        self.logger.handlers.clear()

        self.config = config
        self.cacher = cacher

        self.convert_latex = config['latex']
        self.save_media = config['save_media']
        self.process_media_links = config['process_media_links']
        self.media_save_location = config['data_root'] + config['media_folder']
    
        self.logger.debug(" -- Config Settings -- " +
                     f"\n\tMedia saving: {self.save_media}" +
                     f"\n\t\tMedia save location: {self.media_save_location}" +
                     f"\n\t\tMedia processing: {self.process_media_links}" +
                     f"\n\tLatex conversion: {self.convert_latex}")

        if not os.path.exists(config['data_root']):
            os.makedirs(config['data_root'])

        if self.save_media and not os.path.exists(self.media_save_location):
            os.makedirs(self.media_save_location)

        self.fetches = []

        # internal
        self.__shown_no_token_warning = False

    def limit(self, t=5, limit=3):
        """
        Checks if the number of fetches in the last t seconds is greater than the limit.
        
        If it is, it will return True, otherwise False.
        
        This is a helper used by fetch to prevent too many requests from happening at once. 
        """
        for f in self.fetches:
            if f + t < time.perf_counter():
                self.fetches.remove(f)
        
        if len(self.fetches) > limit:
            sleep(t)
            return True
        else:
            self.fetches.append(time.perf_counter())
            return False

    def fetch(self, url):
        """
        Fetches a page from the internet.
        
        Args:
            url (str): The url to fetch.

        Returns:
            bs4.BeautifulSoup: The naked page soup.

        Raises:
            urllib.error.HTTPError: If the page is not found or rate limited.
            urllib.error.URLError: If the url is invalid.

        """

        if self.limit():
            self.fetch(url)
            return

        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search("wikipedia.org", parsed_url.netloc):
            try:
                req = urllib.request.Request(url)
                try:
                    req.add_header('Authorization', 'Bearer ' + self.config['wiki_api_token'])
                except (ValueError, KeyError, TypeError) as e:
                    if not self.__shown_no_token_warning:
                        self.__shown_no_token_warning = True
                        self.logger.exception("No wiki api token provided. Continuing without one.", exc_info=e)

                response = urllib.request.urlopen(req)
                url = response.geturl()

                page = response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                self.logger.debug(f"{url} is invalid?", exc_info=e)
                # sleep(3)
                # return self.fetch(url)
            except urllib.error.URLError as e:
                self.logger.debug(f"{url} timed out.", exc_info=e)
                #sleep(3)
                #return self.fetch(url)
        else:
            raise ValueError(url)
    
        try:
            page_struct = bs(page, 'html.parser')
            page_struct.url = url
            return page_struct
        except TypeError as e:
            self.logger.debug(f"Failed to parse {url} - likely throttled.", exc_info=e)
            return None

    def retrieve(self, url, page=None):
        """
        Retrieves a page from the internet or cache and parses it into a dictionary 
        for caching and processing.

        Args:
            url (str): The url to retrieve.
            TODO: Deprecate page argument.
            page (bs4.BeautifulSoup): If the page has already been fetched, pass it here.
        """
        if url in self.cacher:
            return model_to_dict(self.cacher.get(url))

        if page is None:
            page = self.fetch(url)
            if page is None:
                return { 'url': url, 'title': None, 'paragraphs': [], 'paragraph_links': [], 'see_also': [], 'toc_links': [], 'references': [], 'media': []}

        paragraphs, para_links = self.__paragraphs(page)

        # Latex conversion to unicode
        if self.convert_latex:
            nl2t = LatexNodes2Text().nodelist_to_text
            paragraphs = [nl2t(LatexWalker(paragraph).get_latex_nodes()[0]) for paragraph in paragraphs]

        media_list = None
        if self.process_media_links:
            media_list = self.__get_media(page) 

        # TODO: define this as a class for typing/API?
        wiki = { 'url': url, 
                'title': page.find(id='firstHeading').get_text(), 
                'paragraphs': paragraphs,
                'paragraph_links': para_links,
                'see_also': self.__see_also(page),
                'toc_links': self.__page_links(page), 
                'references': self.__reference_links(page), 
                'media': media_list}
        
        if self.cacher is not None:
            self.cacher.cache(wiki)
           
        return wiki

    # Wikipedia page parsing
    
    def __paragraphs(self, page):
        """
        Parses the paragraphs from a wikipedia page.
        
        Args: 
            page (bs4.BeautifulSoup): The page to parse.
        """
        paragraphs = []
        paragraph_links = []

        try:
            content_text = page.find(id='mw-content-text')
        except AttributeError as e:
            self.logger.exception(f'Page not set: {page}', exc_info=e)
            return paragraphs, paragraph_links
        
        body_start = content_text.find(attrs={'class': 'mw-parser-output'})
        try:
            for pa in body_start.find_all('p'):     
                text = pa.get_text()
                if text != '' and text != '\n':
                    paragraphs.append(text)

                links = {x.text: "https://en.wikipedia.org" + x['href'] for x in filter(None, [a if a['href'].startswith('/wiki') else None for a in pa.find_all('a')])}
                paragraph_links.append(links)
        except (AttributeError, KeyError) as e:
            self.logger.debug("Missing mw-parser-output - Is this even a wiki page?", exc_info=e)

        return paragraphs, paragraph_links

    def __page_links(self, page):
        """
        Parses the page links from a wikipedia page.

        Args:
            page (bs4.BeautifulSoup): The page to parse.
        """
        links = {}

        try:
            for li in page.find(id='toc').ul.find_all('li'):
                _, name = li.a.get_text().split(' ', 1)
                links[name] = page.url + li.a.get('href')
        except AttributeError as e:
            self.logger.debug("Missing toc?")

        return links

    def __reference_links(self, page):
        """
        Parses the reference links from a wikipedia page.
        
        Args:
            page (bs4.BeautifulSoup): The page to parse.
        """
        references = {}

        content_text = page.find(id='mw-content-text')
    
        try:
            ref_body = content_text.select('.references')[0]
        except IndexError as e:
            self.logger.debug(f"No references.")
            return references # Improperly formatted wiki pages, doesn't have .references.

        for child in ref_body.children:
            if isinstance(child, bs4.element.Tag):
                link = child.find('a', class_='external', recursive=True)
                if link is not None:

                    references[link.text] = link['href']

        return references

    def __see_also(self, page):
        """
        Parses the see also links from a wikipedia page.

        Args:
            page (bs4.BeautifulSoup): The page to parse.
        """
        see_also = {}

        content_text = page.find(id='mw-content-text')
        try:
            sa_soup = content_text.select('.div-col')[0]
        except IndexError as e:
            self.logger.debug("No see also?")

            return see_also

        for a in sa_soup.find_all('a'):
            if a['href'].startswith('/wiki'):
                try:
                    see_also[a['title']] = "https://en.wikipedia.org" + a['href']
                except KeyError as e:
                    self.logger.debug(f"No title for see also link? {a}")
        return see_also

    def __get_media(self, page):
        """
        Parses the media links from a wikipedia page.
        
        Args:
            page (bs4.BeautifulSoup): The page to parse.
            
        Returns:
            A list of media link references.

        Class Variables Used:
            self.save_media: If True, saves the media to disk.
            self.process_media_links (bool): Whether to process media links if not saving.
            self.media_save_path (str): The path to save media to if saving.
        """
        save_locs = []
        dl_urls = []

        if self.process_media_links:
            self.logger.debug("Downloading page media... (This may take a moment.)")
            for img in page.find_all('a', attrs={'class': "image"}):
                url = 'https://en.wikipedia.org/' + img['href']
                # TODO: Fix worker thread blocking.
                dl_page = self.fetch(url)

                dl_link = dl_page.select('.fullMedia')[0].p.a

                dl_url = "https://" + dl_link['href'].lstrip('//')
                save_loc = Path(self.media_save_location, dl_link['title'])

                if not save_loc.exists():
                    save_locs.append(str(save_loc))
                    dl_urls.append(dl_url)

        # Download the media with workers. TODO: Handle with asyncio loop to avoid blocking caller.
        if self.save_media and self.process_media_links:
            try:
                # with Pool(len(dl_urls)) as p:
                #     p.starmap(urllib.request.urlretrieve, zip(dl_urls, save_locs))
                for dl_url, save_loc in zip(dl_urls, save_locs):
                    p = partial(media_retrieve_wrapper, dl_url, save_loc)
                    t = threading.Thread(target=p, daemon=True)
                    self.logger.debug(f"Started downloading {dl_url}.")
                    t.start()
            except urllib.error.HTTPError:
                self.logger.debug(f"Failed to download media from {dl_url}")
                sleep(1)

        return dl_urls


# ----------------------------------------------------------------


def interactive_loop():
    url = None
    db_path = os.getcwd() + '/data/databases/inter_wiki.db'

    with WikiCacher(db_path) as wc:
        crawler = WikiGrabber(cacher=wc)

        while True:
            url = input("wiki url: ")
            if url == "DONE":
                break

            print(crawler.retrieve(url))


def oneshot():
    url = None
    db_path = os.getcwd() + '/data/databases/oneshot_wiki.db'

    with WikiCacher(db_path) as wc:
        crawler = WikiGrabber(cacher=wc)

        print(crawler.retrieve("https://en.wikipedia.org/wiki/Star"))


if __name__ == '__main__':
    try:
        oneshot()
    except KeyboardInterrupt:
        pass