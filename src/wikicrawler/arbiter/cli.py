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

    def handle_search(self, topic, precache=False):
        results = list(self.crawler.search(topic, soup=False, precache=precache))

        if len(results) > 1:
            print_results(results, precache)

        result = select_result(results, precache)

        # compatibility for retrieve/fetch.
        try:
            if isinstance(result, dict):
                url = result['url']
            else:
                url = result.url
        except (KeyError, AttributeError):
            logger.exception(result)
            return

        self.crawl_state['pages'][result['title']] = result

        self.crawl_state['user_choice_stack'].append(result['title'])
        self.crawl_state['page_stack'].append(result['title'])

        if len(results) > 1:
            self.crawl_state['last_search'] = results
            
        analyze_page(result)

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)
            self.crawl_state['pages'][result['title']] = page
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
    
    def handle_result(self):
        if self.crawl_state['last_search'] is not None:
            print_results(self.crawl_state['last_search'], self.search_precaching)
    
    def handle_select(self, idx, precache=False):
        try:
            result = select_result(self.crawl_state['last_search'], precache, int(idx))

            self.crawl_state['pages'][result['title']] = result

            self.crawl_state['user_choice_stack'].append(result['title'])
            self.crawl_state['page_stack'].append(result['title'])

            analyze_page(result)
        except ValueError:
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

                case ['res']:
                    self.handle_result()
                case ['sel', idx]:
                    self.handle_select(idx, precache=self.search_precaching)

                case ['cstate']:
                    print(self.crawl_state)

                case ['exit']:
                    break
                case _: 
                    print(f"Unknown command: {command}")

            self.crawl_state = self.oracle.move(self.crawl_state)



