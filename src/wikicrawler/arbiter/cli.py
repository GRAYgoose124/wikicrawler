import logging
import readline
import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import jaro_winkler_similarity

from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import analyze_page

from .oracle import Oracle
from .utils.other import help_msg
from .utils.search import print_results, select_result


logger = logging.getLogger(__name__)


class WikiPrompt:
    def __init__(self, root_dir, crawler, search_precaching=False):
        # TODO: move to app setup
        nltk.download('wordnet')
        nltk.download('omw-1.4')

        self.search_precaching = search_precaching

        self.crawler = crawler
        self.oracle = Oracle(root_dir, self)

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_colloc': None}
        
    def analyze_page_wrapper(self, page):
        page['freq'], page['colloc'] = analyze_page(page)
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    def handle_search(self, topic):
        results = list(self.crawler.search(topic, soup=False, precache=self.search_precaching))

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

    def handle_state(self, subcmd):
        try:
            match subcmd:
                case ['get_colloc', idx]:
                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]
                    print_results(state['colloc'], True)

                case ['sim_colloc', idx, *phrase]:
                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]

                    most_similar = (0.0, None)
                    for colloc in state['colloc']:
                        colloc = " ".join(colloc)
                        phrase = " ".join(phrase)
                        similarity = jaro_winkler_similarity(colloc, phrase) 
                        # logging.debug(f"{colloc} == {phrase}: {similarity}")

                        if similarity > most_similar[0]:
                            most_similar = (similarity, colloc)

                    self.pointer['most_similar_colloc'] = most_similar[1]
                    print(f"Most similar collocation: {most_similar[1]}")

                case ['get', idx]:
                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]
                    self.analyze_page_wrapper(state)

                case ['list']:
                    print_results(self.crawl_state['pages'].keys(), True)

                case ['res']:
                    print_results(self.crawl_state['last_search'], self.search_precaching)

                case ['sel', idx]:
                    page = select_result(self.crawl_state['last_search'], self.search_precaching, int(idx))

                    self.analyze_page_wrapper(page)
                    self.crawl_state['user_choice_stack'].append(page['title'])
               
                case _:
                    pass
        except (ValueError, IndexError) as e:
            logging.exception("Handle_state choice error.", exc_info=e)

    def handle_divine(self, jump_phrase):
        self.oracle.move(jump_phrase)

    def handle_similarity_jump(self, subcmd):
        match subcmd:
            case _:
                pass

    def loop(self):
        command = ""

        while command != "exit":
            command = input("> ")
            
            self.parse_cmd(command)
  
    def parse_cmd(self, command):
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

            case ['div', *jump_phrase]:
                self.handle_divine(" ".join(jump_phrase))

            case ['tsym']:
                self.handle_similarity_jump()

            case ['pointer']:
                print(self.pointer)

            case ['help']:
                print(*help_msg, sep='\n')
            case ['exit']:
                pass
            case _: 
                print(f"Unknown command: {command}")
