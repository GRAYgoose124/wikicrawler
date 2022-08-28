import os
from pathlib import Path
import urllib.request
import urllib.parse
import bs4
from bs4 import BeautifulSoup as bs
import json

import re 
import threading

from cacher import WikiCacher

# import nltk
# import tensorflow, numpy, etc
# import networkx, matplotlib, plotly


# TODO: Rename this a "Grabber" so the crawler can traverse.
class WikiGrabber:
    wiki_regex = re.compile("^https*://.*\.wikipedia\.org.*")
    link_regex = re.compile("^https*://.*\..*")
    header_regex = re.compile('^h[1-6]$')

    def __init__(self, cacher=None):
        self.cacher = cacher

    def retrieve(self, url):
        # TODO: Add optional nodb keyword.
        page = self.__visit(url)

        paragraphs, para_links = self.__paragraphs(page)

        wiki = { 'url': url, 
                'title': page.find(id='firstHeading').get_text(), 
                'paragraphs': paragraphs,
                'paragraph_links': para_links,
                'see_also': self.__see_also(page),
                'toc_links': self.__page_links(page), 
                'references': self.__reference_links(page), 
                'media': self.__get_media(page) }

        if self.cacher is not None:
            self.cacher.cache(wiki)
            
        return wiki

    def __visit(self, url):
        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search("wikipedia.org", parsed_url.netloc):
            page = urllib.request.urlopen(url).read().decode("utf-8")
        else:
            raise ValueError(url)
    
        page_struct = bs(page, 'html.parser')
        page_struct.url = url
        return page_struct

    def __paragraphs(self, page):
        # rip paragraphs - TODO:get links from paragraph too
        paragraphs = []
        paragraph_links = []

        content_text = page.find(id='mw-content-text')
        body_start = content_text.find(attrs={'class': 'mw-parser-output'})
        for pa in body_start.find_all('p'):     
            text = pa.get_text()
            if text != '' and text != '\n':
                paragraphs.append(text)

            links = {x.text: x['href'] for x in filter(None, [a if a['href'].startswith('/wiki') else None for a in pa.find_all('a')])}
            paragraph_links.append(links)

        return paragraphs, paragraph_links

    def __page_links(self, page):
        links = {}

        try:
            for li in page.find(id='toc').ul.find_all('li'):
                _, name = li.a.get_text().split(' ', 1)
                links[name] = page.url + li.a.get('href')
        except AttributeError:
            pass # TODO: This this exception is thrown - it means there's no toc.

        return links

    def __reference_links(self, page):
        # rip references
        references = {}

        content_text = page.find(id='mw-content-text')
    
        try:
            ref_body = content_text.select('.references')[0]
        except IndexError:
            # TODO: Proper debug logging on all BS exceptions.
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
        sa_soup = content_text.select('.div-col')
        if sa_soup is None or len(sa_soup) == 0:
            try:
                sa_soup = content_text.find(id='See_also').parent.nextSibling.nextSibling.children
            except:
                return see_also # Likely just doesn't exist.

        for c in sa_soup:
            if isinstance(c, bs4.element.Tag):
                see_also[c.a['title']] = "https://en.wikipedia.org" + c.a['href']

        return see_also

    def __links_per_paragraph(self, paragraphs):
        links = []

        # NOTE: won't work as is, paragraphs get filtered by get_text
        for para in paragraphs:
            links.append()

    def __get_media(self, page):
        paths = []
        for img in page.find_all('a', attrs={'class': "image"}):
            url = 'https://en.wikipedia.org/' + img['href']
            # TODO: Fix worker thread blocking.
            dl_page = self.__visit(url)

            dl_link = dl_page.select('.fullMedia')[0].p.a
            dl_path = Path(os.getcwd() + '/images', dl_link['title'])

            if not dl_path.exists():
                dl_url = "https://" + dl_link['href'].lstrip('//')
                t = threading.Thread(target=lambda: urllib.request.urlretrieve(dl_url, dl_path), args=(), daemon=True)
                t.start()

            paths.append(str(dl_path))
        
        return paths

    def __follow_page_re(self):
        pass


# ----------------------------------------------------------------


def interactive_loop():
    url = None
    db_path = os.getcwd().rsplit('/', 1)[0] + '/databases/inter_wiki.db'

    with WikiCacher(db_path) as wc:
        crawler = WikiGrabber(cacher=wc)

        while True:
            url = input("wiki url: ")
            if url == "DONE":
                break

            print(crawler.retrieve(url))


def oneshot():
    url = None
    db_path = os.getcwd() + '/databases/oneshot_wiki.db'

    print(db_path)
    with WikiCacher(db_path) as wc:
        crawler = WikiGrabber(cacher=wc)

        print(crawler.retrieve("https://en.wikipedia.org/wiki/Q.E.D."))


if __name__ == '__main__':
    try:
        oneshot()
    except KeyboardInterrupt:
        pass