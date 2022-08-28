import os
import re
import requests

import urllib.request
import urllib.parse
import bs4
from bs4 import BeautifulSoup as bs

from grabber import WikiGrabber
from cacher import WikiCacher
from parasentiment import analyze_page, parse_page


lang_code = "en"
base_url = f"https://{lang_code}.wikipedia.org"


def fetch(url):
    response = urllib.request.urlopen(url)
    soup = bs(response, 'html.parser')
    soup.url = url

    return soup


def catlinks(page):
    categories = {}
    
    for link in page.find(id="catlinks", class_="catlinks").find_all('a'):
        categories[link['title']] = link['href']
    return categories


def disambiglinks(page):
    links = {}
    """This function assumes that it's being passed an identified disambiguation page."""
    for link in page.select('.mw-parser-output')[0].find_all('a'):
        try:
            if link['href'].startswith('/wiki/'):
                links[link['title']] = link['href']
        except KeyError:
            pass

    return links


def wikisearch(phrase):
    search_url = f"{base_url}/wiki/Special:Search?search={urllib.parse.quote(phrase, safe='')}&"

    soup = fetch(search_url)

    # handle disambiguation
    categories = catlinks(soup)
    if any(["Disambiguation" in cat for cat in categories]):
        options = list(disambiglinks(soup).values())
        soup = options

    return soup


def wikifetch(phrase):
    results = wikisearch(phrase)

    if isinstance(results, list):
        for result in results:
            yield fetch(base_url + result)
    else:
        yield fetch(base_url + result)

    return

if __name__ == '__main__':
    for result in wikifetch(input("Wiki search: ")):
        print(result.url)
