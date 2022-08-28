from crawler import WikiCrawler
from para import analyze_page, parse_page


class WikiHopper:
    def traverse(self, url):
        path = []

        current_url = url
        with WikiCrawler('wikipedia.db') as wc:
            page = wc.retrieve(current_url)
            



if __name__ == '__main__':
    hopper = WikiHopper()
