import argparse
import os

from core.crawler import WikiCrawler
from core.db.cacher import WikiCacher


class WikiPrompt:
    def __init__(self, crawler):
        self.crawler = crawler
        self.crawl_state = None

    def handle_search(self, topic):
        pass
    
    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = crawler.retrieve(url)
        else:
            print("Invalid Wikipedia url.")

    def handle_more(self):
        pass

    def handle_less(self):
        pass

    def handle_about(self, topic):
        pass

    def loop(self):
        command = ""

        while command != "exit":
            command = input("> ")

            match command.split():
                case ['search', *phrase]: 
                    self.handle_search(" ".join(phrase))
                case ['url', url]:
                    self.handle_url(url)
                case ['more']:
                    self.handle_more()
                case ['less']:
                    self.handle_less()
                case ['about', *topic]:
                    self.handle_about(" ".join(topic))
                case ['exit']:
                    break
                case _: 
                    print(f"Unknown command: {command}")


if __name__ == '__main__':
    with WikiCacher(os.getcwd() + '/data/databases/cli.db') as wc:
        crawler = WikiCrawler(cacher=wc)
        prompt = WikiPrompt(crawler=crawler)

        prompt.loop()