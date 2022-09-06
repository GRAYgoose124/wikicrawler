import logging

from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import analyze_page

from .oracle import Oracle


logger = logging.getLogger(__name__)


def print_results(results, precache):
    for idx, res in enumerate(results):
        if not precache:
            print(f"{idx}: {res[0]}")
        else:
            print(f"{idx}: {res['title']}")


def select_result(results, precache, index=None):
    if len(results) > 1:
        try:
            if index is None:
                selected = None
                while selected is None:
                    selected = int(input("Choose a result: "))
            else:
                selected = index

            if not precache:
                result = results[selected][1]()
            else:
                result = results[selected]


        except ValueError as e:
            pass
    else:
        result = results[0]

    return result


class WikiPrompt:
    def __init__(self, root_dir, crawler, search_precaching=False):
        self.search_precaching = search_precaching

        self.crawler = crawler
        self.oracle = Oracle(root_dir)

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pages': {}, 'last_search': None}

    def analyze_page_wrapper(self, page):
        page['freq'], page['colloc'] = analyze_page(page)
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    def handle_search(self, topic):
        results = list(self.crawler.search(topic, soup=False, precache=self.search_precaching))

        if len(results) > 1:
            print_results(results, self.search_precaching)

        page = select_result(results, self.search_precaching)

        self.analyze_page_wrapper(page)
        self.crawl_state['user_choice_stack'].append(page['title'])

        if len(results) > 1:
            self.crawl_state['last_search'] = results
        else:
            self.crawl_state['last_search'] = [page]

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)

            self.analyze_page_wrapper(page)
        else:
            print("Invalid Wikipedia url.")
        
    def handle_more(self):
        pass

    def handle_less(self):
        pass

    def handle_about(self, topic):
        pass
    
    def handle_result(self):
        if self.crawl_state['last_search'] is not None:
            print_results(self.crawl_state['last_search'], self.search_precaching)
    
    def handle_state(self, subcmd):
        try:
            match subcmd:
                case ['get', idx]:
                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]
                    print(state)

                case ['list']:
                    print_results(self.crawl_state['pages'].keys(), False)

                case ['res']:
                    print_results(self.crawl_state['last_search'], self.search_precaching)

                case ['sel', idx]:
                    page = select_result(self.crawl_state['last_search'], self.search_precaching, int(idx))

                    self.analyze_page_wrapper(page)
                    self.crawl_state['user_choice_stack'].append(page['title'])
               
                case _:
                    pass
        except (ValueError, IndexError):
            pass

    def handle_divine(self):
        self.crawl_state = self.oracle.move(self.crawl_state)

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

                case ['st', *subcmd]:
                    self.handle_state(subcmd)

                case ['div']:
                    self.handle_divine()

                case ['cstate']:
                    print(self.crawl_state)

                case ['exit']:
                    break
                case _: 
                    print(f"Unknown command: {command}")
