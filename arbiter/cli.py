import os

from core.crawler import WikiCrawler
from core.sentiment.paragraph import analyze_page

from arbiter.oracle import Oracle


class WikiPrompt:
    def __init__(self, crawler):
        self.crawler = crawler
        self.oracle = Oracle(os.getcwd() + "/data/oracle/config.json")
        self.crawl_state = {'page': None}

    def handle_search(self, topic):
        results = list(self.crawler.search(topic, soup=False))

        if len(results) > 1:
            for idx, result in enumerate(results):
                print(f"{idx}: {result.title}")
            
            try:
                selected = None
                while selected is None:
                    selected = int(input("Choose a result: "))
                
                analyze_page(results[selected])
            except ValueError:
                pass
        else:
            analyze_page(results[0])

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)
            self.crawl_state['page'] = page

            analyze_page(page)
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
                case ['s', *phrase]: 
                    self.handle_search(" ".join(phrase))
                case ['u', url]:
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

            self.crawl_state = self.oracle.move(self.crawl_state)



