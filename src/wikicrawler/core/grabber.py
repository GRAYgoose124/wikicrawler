from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from multiprocessing import Pool
import os
import json
import urllib
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


logger = logging.getLogger(__name__)


def retrieve_wrapper(dl_url, save_loc):
    try:
        urllib.request.urlretrieve(dl_url, save_loc)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        # logger.debug("Failed to download media. - Likely rate limited.")
        sleep(5)
        retrieve_wrapper(dl_url, save_loc)


# TODO: make grabber asyncronous
class WikiGrabber:
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*\..*")
    header_regex = re.compile('^h[1-6]$')

    def __init__(self, config, cacher=None):
        self.config = config
        self.cacher = cacher

        self.convert_latex = config['latex']
        self.save_media = config['save_media']
        self.process_media_links = config['process_media_links']
        self.media_save_location = config['data_root'] + config['media_folder']
    
        if not os.path.exists(config['data_root']):
            os.makedirs(config['data_root'])

        if self.save_media and not os.path.exists(self.media_save_location):
            os.makedirs(self.media_save_location)

    def fetch(self, url):
        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search("wikipedia.org", parsed_url.netloc):
            try:
                response = urllib.request.urlopen(url)
                url = response.geturl()
                page = response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                logger.debug(f"{url} is invalid?", exc_info=e)
                sleep(1)
            except urllib.error.URLError as e:
                logger.debug(f"{url} timed out.", exc_info=e)
                sleep(1)
                return self.fetch(url)
        else:
            raise ValueError(url)
    
        page_struct = bs(page, 'html.parser')
        page_struct.url = url
        return page_struct

    def retrieve(self, url, page=None):
        # TODO: Add optional nodb keyword.

        if url in self.cacher:
            return model_to_dict(self.cacher.get(url))

        if page is None:
            # TODO: asyncronous?
            page = self.fetch(url)

        paragraphs, para_links = self.__paragraphs(page)

        # Latex conversion to unicode
        if self.convert_latex:
            nl2t = LatexNodes2Text().nodelist_to_text
            paragraphs = [nl2t(LatexWalker(paragraph).get_latex_nodes()[0]) for paragraph in paragraphs]

        media_list = None
        if self.process_media_links:
            media_list = self.__get_media(page) 

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
        paragraphs = []
        paragraph_links = []

        content_text = page.find(id='mw-content-text')
        body_start = content_text.find(attrs={'class': 'mw-parser-output'})
        try:
            for pa in body_start.find_all('p'):     
                text = pa.get_text()
                if text != '' and text != '\n':
                    paragraphs.append(text)

                links = {x.text: "https://en.wikipedia.org" + x['href'] for x in filter(None, [a if a['href'].startswith('/wiki') else None for a in pa.find_all('a')])}
                paragraph_links.append(links)
        except (AttributeError, KeyError) as e:
            logger.debug("Missing mw-parser-output - Is this even a wiki page?")

        return paragraphs, paragraph_links

    def __page_links(self, page):
        links = {}

        try:
            for li in page.find(id='toc').ul.find_all('li'):
                _, name = li.a.get_text().split(' ', 1)
                links[name] = page.url + li.a.get('href')
        except AttributeError as e:
            logger.debug("Missing toc?")

        return links

    def __reference_links(self, page):
        # rip references
        references = {}

        content_text = page.find(id='mw-content-text')
    
        try:
            ref_body = content_text.select('.references')[0]
        except IndexError as e:
            logger.debug(f"No references.")
            return references # Improperly formatted wiki pages, doesn't have .references.

        for child in ref_body.children:
            if isinstance(child, bs4.element.Tag):
                link = child.find('a', class_='external', recursive=True)
                if link is not None:

                    references[link.text] = link['href']

        return references

    def __see_also(self, page):
        # rip see also
        see_also = {}

        content_text = page.find(id='mw-content-text')
        try:
            sa_soup = content_text.select('.div-col')[0]
        except IndexError as e:
            logger.debug("No see also?")

            return see_also

        for a in sa_soup.find_all('a'):
            if a['href'].startswith('/wiki'):
                try:
                    see_also[a['title']] = "https://en.wikipedia.org" + a['href']
                except KeyError as e:
                    logger.debug(f"No title for see also link? {a}")
        return see_also

    def __get_media(self, page):
        save_locs = []
        dl_urls = []

        if self.process_media_links:
            logger.debug("Downloading page media... (This may take a moment.)")
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
                    p = partial(retrieve_wrapper, dl_url, save_loc)
                    t = threading.Thread(target=p, daemon=True)
                    logger.debug(f"Started downloading {dl_url}.")
                    t.start()
            except urllib.error.HTTPError:
                logger.debug(f"Failed to download media from {dl_url}")
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