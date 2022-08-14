import urllib.request
import urllib.parse
from bs4 import BeautifulSoup as bs
import json
from db import DBMan, declarative_base, Column, Integer, Text
import re 

# import nltk
# import tensorflow, numpy, etc
# import networkx, matplotlib, plotly





def get_wiki_page(wiki_url):
    parsed_url = urllib.parse.urlparse(wiki_url)

    if re.search("wikipedia.org", parsed_url.netloc):
        return urllib.request.urlopen(wiki_url).read().decode("utf-8")
    else:
        return None


class WikiCrawler:
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*")
    header_regex = re.compile('^h[1-6]$')

    def __enter__(self):
        Base = declarative_base()

        class DBEntry(Base):
            __tablename__ = 'wikipages'
            id = Column(Integer, primary_key=True)
            url = Column(Text, nullable=False)
            page = Column(Text, nullable=False)
            title = Column(Text, nullable=False)
            paragraphs = Column(Text, nullable=False)
            sub_headings = Column(Text, nullable=False)
            internal_links = Column(Text, nullable=False)
            wiki_links = Column(Text, nullable=False)
            referencess = Column(Text, nullable=False)
            media = Column(Text, nullable=False)

        self.manager = DBMan('wikipedia.db', Base, DBEntry)
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
        wiki['sub_headings'], wiki['internal_links'] = self._page_links(wiki['url'], wiki['page'])
        wiki['wiki_links'] = self._wiki_links(wiki['page'])
        wiki['references'] = self._reference_links(wiki['page'])
        wiki['media'] = self._get_media(wiki['page'])

        if self.manager is not None:
            entry = self.manager.Node(url = wiki['url'], page = str(wiki['page'].contents), title = wiki['title'], paragraphs = wiki['paragraphs'], 
                                            sub_headings = wiki['sub_headings'], internal_links = wiki['internal_links'], 
                                            wiki_links = wiki['wiki_links'], referencess = wiki['references'], media = wiki['media'])

            self.manager.session.add(entry)

        return wiki

    def _visit(self, url):
        page = get_wiki_page(url)
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
        sub_headings = {}
        links = []

        for li in page.find(id='toc').ul.find_all('li'):
            index, name = li.a.get_text().split(' ', 1)
            index = str(index)
            sub_headings[index] = (name, li.a.get('href'))
            links.append(url + sub_headings[index][1])

        return sub_headings, links

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

    def _get_media(self, page):
        pass

    def _follow_page_ref(self):
        pass

def interactive_loop():
    url = None

    while url != "!quit":
        url = input("wiki url: ")
        wc = WikiCrawler(url)
        print(wc.title, '\n', wc.summary)


if __name__ == '__main__':
    pages = ['http://en.wikipedia.org/wiki/Philosophy', 'https://en.wikipedia.org/wiki/Existence']
    
    with WikiCrawler() as wc:
        wc.crawl(pages[1])
   