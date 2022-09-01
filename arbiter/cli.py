import os

from core.crawler import WikiCrawler
from core.sentiment.paragraph import analyze_page

from arbiter.oracle import Oracle


class WikiPrompt:
    def __init__(self, crawler):
        self.crawler = crawler
        self.oracle = Oracle(os.getcwd() + "/data/oracle/config.json")
        self.crawl_state = None

    def handle_search(self, topic):
        pass
    
    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)
            paragraph_sentiment = analyze_page(page)
        else:
            print("Invalid Wikipedia url.")

    def handle_more(self):
        pass

    def handle_less(self):
        pass

    def handle_about(self, topic):
        pass

    def start_loop(self):
        for frame in self.prompt_loop():
            self.oracle.see(frame)

    def prompt_loop(self):

        command = ""
        while command != "exit":
            command = input("> ")

            match command.split():
                case ['search', *phrase]: 
                    yield self.handle_search(" ".join(phrase))
                case ['url', url]:
                    yield self.handle_url(url)
                case ['more']:
                    yield self.handle_more()
                case ['less']:
                    yield self.handle_less()
                case ['about', *topic]:
                    yield self.handle_about(" ".join(topic))
                case ['exit']:
                    break
                case _: 
                    print(f"Unknown command: {command}")

        return


