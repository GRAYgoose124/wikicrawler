from io import TextIOWrapper
import os
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
            self.crawl_state['last_search'] = [results]

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)

            self.analyze_page_wrapper(page)
        else:
            print("Invalid Wikipedia url.")
        
    def handle_state(self, subcmd):
        try:
            match subcmd:
                case ['get_colloc', idx]:
                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]
                    print_results(state['colloc'], True)

                case ['sim_colloc', idx, *phrase]:
                    phrase = " ".join(phrase)

                    state = self.crawl_state['pages'][self.crawl_state['page_stack'][int(idx)]]

                    most_similar = (0.0, None)
                    for colloc in state['colloc']:
                        colloc = " ".join(colloc)
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

    def handle_colloc_move(self, jump_phrase):
        self.run_script(f"st sim_colloc 0 {jump_phrase}",
                        f"s {self.pointer['most_similar_colloc']}",
                         "st sel 0")

    def parse_cmd(self, command):
        match command.split():
            case ['s', *phrase]: 
                self.handle_search(" ".join(phrase))

            case ['u', url]:
                self.handle_url(url)

            case ['st', *subcmd]:
                self.handle_state(subcmd)

            case ['cmov', *jump_phrase]:
                self.handle_colloc_move(" ".join(jump_phrase))

            case ['pointer']:
                print(self.pointer)

            case ['help']:
                print(*help_msg, sep='\n')
            case ['exit']:
                pass

            case _: 
                print(f"Unknown command: {command}")

    def loop(self):
        command = ""

        while command != "exit":
            command = input("> ")
            
            self.parse_cmd(command)

    def run_script(self, *script_or_path):
        if len(script_or_path) == 1:
            script_or_path = script_or_path[0]
            # check for script at path
            if os.path.exists(script_or_path):
                with open(script_or_path, 'r') as script:
                    for command in script:
                        self.parse_cmd(command)
            # see if it's just a file object
            elif isinstance(script_or_path, TextIOWrapper):
                for command in script_or_path:
                    self.parse_cmd(command)
            # or try to split the string by \n
            elif '\n' in script_or_path:
                for command in script_or_path.split('\n'):
                    self.parse_cmd(command)
        # otherwise check if it's a list of commands
        elif (isinstance(script_or_path, tuple)
         and len(script_or_path) > 1
         and isinstance(script_or_path[0], str)):
            for command in script_or_path:
                self.parse_cmd(command)
