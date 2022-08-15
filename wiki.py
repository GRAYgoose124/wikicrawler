import os
from pathlib import Path
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup as bs
import json
from db import DBMan, Column, Text, JSON, Base
import re 

# import nltk
# import tensorflow, numpy, etc
# import networkx, matplotlib, plotly

class DBEntry(Base):
    __tablename__ = 'wikipages'
    # id = Column(Integer)
    url = Column(Text, nullable=False, primary_key=True)
    title = Column(Text, nullable=False)
    paragraphs = Column(JSON, nullable=False)
    internal_links = Column(JSON, nullable=False)
    wiki_links = Column(JSON, nullable=False)
    references = Column(JSON, nullable=False)
    media = Column(JSON, nullable=False)


class WikiCrawler:
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*\..*")
    header_regex = re.compile('^h[1-6]$')

    def __init__(self, db_name):
        self.manager = None
        self.db_name = db_name

    def __enter__(self):
        self.manager = DBMan(self.db_name, DBEntry)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.close()
        self.manager = None

    def crawl(self, url):
        wiki = {}
        wiki['url'] = url
        wiki['page'] = self._visit(wiki['url'])

        wiki['title'] = wiki['page'].find(id='firstHeading').get_text()
        wiki['paragraphs'] = self._paragraphs(wiki['page'])
        wiki['internal_links'] = self._page_links(wiki['url'], wiki['page'])
        wiki['wiki_links'] = self._wiki_links(wiki['page'])
        wiki['references'] = self._reference_links(wiki['page'])
        wiki['media'] = self._get_media(wiki['page'])

        if self.manager is not None:
            entry = self.manager.Node(url = wiki['url'], title = wiki['title'], paragraphs = (wiki['paragraphs']), 
                                        internal_links = (wiki['internal_links']), wiki_links = (wiki['wiki_links']), 
                                        references = (wiki['references']), media = (wiki['media']))

            self.manager.session.merge(entry)

        return wiki

    def _visit(self, url):
        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search("wikipedia.org", parsed_url.netloc):
            page = urllib.request.urlopen(url).read().decode("utf-8")
    
        page_struct = bs(page, 'html.parser')
        return page_struct

    def _paragraphs(self, page):
        paragraphs = []
        body_start = page.find(id='mw-content-text').\
            find(attrs={'class': 'mw-parser-output'})

        for pa in body_start.find_all('p'):     
            text = pa.get_text()
            if text != '' and text != '\n':
                paragraphs.append(text)
        
        return paragraphs

    def _page_links(self, url, page):
        links = {}

        for li in page.find(id='toc').ul.find_all('li'):
            _, name = li.a.get_text().split(' ', 1)
            links[name] = url + li.a.get('href')

        return links

    def _wiki_links(self, page):
        extern = []

        for wikilink in page.find_all('a', attrs={'href': self.wiki_regex}):
            extern.append(wikilink.get('href'))

        return extern

    def _reference_links(self, page):
        links = []

        for a in page.find_all('a', attrs={'class': 'external text', 'href': self.link_regex}):
            links.append((a['href'], a.get_text())) 

        return links

    def _links_per_paragraph(self, paragraphs):
        pass

    def _get_media(self, page):
        paths = []
        for img in page.find_all('a', attrs={'class': "image"}):
            # TODO: Needs to create a bs to get the fi
            url = 'https://en.wikipedia.org/' + img['href']
            dl_page = self._visit(url)

            dl_link = dl_page.select('.fullMedia')[0].p.a
            dl_path = Path('images', dl_link['title'])

            if not dl_path.exists():
                dl_url = "https://" + dl_link['href'].lstrip('//')
                urllib.request.urlretrieve(dl_url, dl_path)

            paths.append(str(dl_path))
        
        return paths

    def _follow_page_ref(self):
        pass


def interactive_loop():
    url = None

    with WikiCrawler('interactive_wiki.db') as wc:
        while url != "DONE":
            url = input("wiki url: ")
            wc.crawl(url)


def crawl_loop(urls):
    with WikiCrawler('wikipedia.db') as wc:
        for url in urls:
            wc.crawl(url)
   

if __name__ == '__main__':
    # interactive_loop()

    urls = ['http://en.wikipedia.org/wiki/Philosophy', 'https://en.wikipedia.org/wiki/Existence']
    
    crawl_loop(urls)
