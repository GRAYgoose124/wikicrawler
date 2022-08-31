import argparse
import os

from core.grabber import WikiGrabber
from core.db.cacher import WikiCacher

from core.sentiment.paragraph import analyze_page, parse_page
from utils.other import license_str


def updatedb(path):
    pages = {}

    urls = []
    with open(path) as f:
        for line in f:
            # urls if you want to print on start history
            urls.append(line)

    with WikiCacher(os.getcwd() + '/data/databases/parasentimentwiki.db') as wc:
        crawler = WikiGrabber(cacher=wc)
        # TODO: Store timestamps and update after X interval or after db file modification date.
        for url in urls:            
            page = crawler.retrieve(url)

            pages[page['title']] = page

            analyze_page(page)

    return pages


def oneshot(url):
    if WikiGrabber.wiki_regex.match(url):
        with WikiCacher(os.getcwd() + '/data/databases/parasentimentwiki.db') as wc:
            crawler = WikiGrabber(cacher=wc)

            page = crawler.retrieve(url)
            analyze_page(page)

        with open('urls.txt', 'a+') as f:
            if url not in f:
                f.write(url + '\n')    
    else: 
        print("Invalid URL!")


def main():
    parser = argparse.ArgumentParser(description="Digest wikipedia articles.", epilog=license_str)
    parser.add_argument('url', action='store', nargs='?', type=str, help=f"URL of wikipedia article to digest.")

    args = parser.parse_args()
    url = args.url

    if args.url:
        print(f"Looking up {args.url}...")
        oneshot(url)
    else:
        print("Updating db with urls.txt...")
        updatedb(os.getcwd() + '/data/urls.txt')


if __name__ == '__main__' :
    try:
        main()
    except KeyboardInterrupt:
        pass