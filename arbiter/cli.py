import os

from core.crawler import WikiCrawler
from core.sentiment.paragraph import analyze_page

from arbiter.oracle import Oracle


class WikiPrompt:
    def __init__(self, root_dir, crawler, search_precaching=False):
        self.search_precaching = search_precaching

        self.crawler = crawler
        self.oracle = Oracle(root_dir)

        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pages': {}}

    def handle_search(self, topic, precache=False):
        result = None
        results = list(self.crawler.search(topic, soup=False, precache=precache))

        if len(results) > 1:
            for idx, res in enumerate(results):
                if not precache:
                    print(f"{idx}: {res[0]}")
                else:
                    print(f"{idx}: {res['title']}")
            
            try:
                selected = None
                while selected is None:
                    selected = int(input("Choose a result: "))
                
                if not precache:
                    result = results[selected][1]()
                else:
                    result = results[selected]

            except ValueError:
                pass
        else:
            result = results[0]

        # compatibility for retrieve/fetch.
        if isinstance(result, dict):
            url = result['url']
        else:
            url = result.url

        self.crawl_state['pages'][result['title']] = result

        self.crawl_state['user_choice_stack'].append(result['title'])
        self.crawl_state['page_stack'].append(result['title'])

        analyze_page(result)

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)
            self.crawl_state['page_stack'].append(page['title'])

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
                    self.handle_search(" ".join(phrase), precache=self.search_precaching)
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



