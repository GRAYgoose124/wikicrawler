import os
from pathlib import Path
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup as bs
import json
from sqlalchemy.exc import NoResultFound
from model_to_dict import model_to_dict
from db import DBMan, Column, Text, JSON, Base
import re 
import threading

# import nltk
# import tensorflow, numpy, etc
# import networkx, matplotlib, plotly


class DBWikiPageEntry(Base):
    __tablename__ = 'wikipages'
    # id = Column(Integer)
    url = Column(Text, nullable=False, primary_key=True)
    title = Column(Text, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    internal_links = Column(JSON, nullable=False) # TODO: rename to toc_links
    wiki_links = Column(JSON, nullable=False)
    references = Column(JSON, nullable=False)
    media = Column(JSON, nullable=False)
    stats = Column(JSON, nullable=True)


class WikiCrawler:
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*\..*")
    header_regex = re.compile('^h[1-6]$')

    def __init__(self, db_name):
        self.manager = None
        self.db_name = db_name

    def __enter__(self):
        self.manager = DBMan(self.db_name, DBWikiPageEntry)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.close()
        self.manager = None

    def __contains__(self, url):
        try:
            self.manager.session.query(self.manager.Node).filter(self.manager.Node.url == url).one()
            return True
        except NoResultFound:
            return False

    def retrieve(self, url, force_update=False):
        # TODO: Add optional nodb keyword.
        # TODO: Add raw `page` save to file. symlink to it in wiki['cached'] or similar
        try:
            if force_update: # TODO: Timestamp field and auto-update after X interval.
                raise NoResultFound("Forcing page update...")

            return model_to_dict(self.manager.session.query(self.manager.Node).filter(self.manager.Node.url == url).one())
        except NoResultFound:
            page = self.__visit(url)
            wiki = { 'url': url, 
                    'title': page.find(id='firstHeading').get_text(), 
                    'paragraphs': self.__paragraphs(page),
                    'internal_links': self.__page_links(url, page), 
                    'wiki_links': self.__wiki_links(page), 
                    'references': self.__reference_links(page), 
                    'media': self.__get_media(page) }

            if self.manager is not None:    
                print(f"Caching {url}...")
                self.manager.session.merge(self.manager.Node(**wiki))

            return wiki

    def __visit(self, url):
        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search("wikipedia.org", parsed_url.netloc):
            page = urllib.request.urlopen(url).read().decode("utf-8")
        else:
            raise ValueError(url)
    
        page_struct = bs(page, 'html.parser')
        return page_struct

    def __paragraphs(self, page):
        paragraphs = []

        body_start = page.find(id='mw-content-text').find(attrs={'class': 'mw-parser-output'})
        for pa in body_start.find_all('p'):     
            text = pa.get_text()
            if text != '' and text != '\n':
                paragraphs.append(text)
        
        return paragraphs

    def __page_links(self, url, page):
        links = {}

        try:
            for li in page.find(id='toc').ul.find_all('li'):
                _, name = li.a.get_text().split(' ', 1)
                links[name] = url + li.a.get('href')
        except AttributeError:
            pass # TODO: This this exception is thrown - it means there's no toc.

        return links

    def __wiki_links(self, page):
        links = []

        for wikilink in page.find_all('a', attrs={'href': self.wiki_regex}):
            links.append(wikilink.get('href'))

        return links

    def __reference_links(self, page):
        links = []

        # TODO: Follow cite_notes to properly associate with paragraphs.
        for a in page.find_all('a', attrs={'class': 'external text', 'href': self.link_regex}):
            links.append((a['href'], a.get_text())) 

        return links

    def __links_per_paragraph(self, paragraphs):
        links = []

        for para in paragraphs:
            links.append()

    def __get_media(self, page):
        paths = []
        for img in page.find_all('a', attrs={'class': "image"}):
            url = 'https://en.wikipedia.org/' + img['href']
            # TODO: Move retrieval to worker thread.G121
            dl_page = self.__visit(url)

            dl_link = dl_page.select('.fullMedia')[0].p.a
            dl_path = Path('/home/goose/Documents/coding/current_lesser/wikiwebber/wikiwebber/images', dl_link['title'])

            if not dl_path.exists():
                dl_url = "https://" + dl_link['href'].lstrip('//')
                t = threading.Thread(target=lambda: urllib.request.urlretrieve(dl_url, dl_path), args=(), daemon=True)
                t.start()

            paths.append(str(dl_path))
        
        return paths

    def __follow_page_re(self):
        pass


def interactive_loop():
    url = None

    with WikiCrawler('interactive_wiki.db') as wc:
        while url != "DONE":
            url = input("wiki url: ")
            print(wc.retrieve(url))


if __name__ == '__main__':
    interactive_loop()
