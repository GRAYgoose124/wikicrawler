import urllib.request
import urllib.parse
from bs4 import BeautifulSoup as bs
import json
from db import DBMan
import re 

# import nltk
# import tensorflow, numpy, etc
# import networkx, matplotlib, plotly


manager = DBMan()
session = manager.session


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

    def __init__(self, url):
        self.crawl(url)

    def crawl(self, url):
        self.url = url
        self.page = self._visit(self.url)

        self.title = self.page.find(id='firstHeading').get_text()
        self.sub_headings = {}
        self.paragraphs = self._paragraphs()
        self.internal_links = self._page_links()
        self.wiki_links = self._wiki_links()
        self.references = self._reference_links()
        self.media = self._get_media()

    def _visit(self):
        page = get_wiki_page(self.url)
        page_struct = bs(page, 'html.parser')

        return page_struct

    def _paragraphs(self):
        paragraphs = []
        body_start = self.page.find(id='mw-content-text').\
            find(attrs={'class': 'mw-parser-output'})

        for pa in body_start.find_all('p'):     
            text = pa.get_text()
            if text != '' and text != '\n':
                paragraphs.append(text)
        
        return paragraphs

    def _page_links(self):
        links = []

        for li in self.page.find(id='toc').ul.find_all('li'):
            index, name = li.a.get_text().split(' ', 1)
            index = str(index)
            self.sub_headings[index] = (name, li.a.get('href'))
            links.append(self.url + self.sub_headings[index][1])

        return links

    def _wiki_links(self):
        extern = []

        for wikilink in self.page.find_all('a', attrs={'href': self.wiki_regex}):
            extern.append(wikilink.get('href'))

        return extern

    def _reference_links(self):
        links = []

        for a in self.page.find_all('a', attrs={'class': 'external text', 'href': self.link_regex}):
            links.append((a['href'], a.get_text())) 

        return links

    def _get_media(self):
        pass

    def _follow_page_ref(self):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str((self.title, self.sub_headings, self.paragraphs, self.internal_links, self.wiki_links, self.references, self.media))

def interactive_loop():
    url = None

    while url != "!quit":
        url = input("wiki url: ")
        wc = WikiCrawler(url)
        print(wc.title, '\n', wc.summary)


if __name__ == '__main__':
    pages = ['http://en.wikipedia.org/wiki/Philosophy', 'https://en.wikipedia.org/wiki/Existence']
    parser = WikiCrawler(pages[1])
    # # print(parser.body)
    # print(parser.sub_headings)
    print(parser)
