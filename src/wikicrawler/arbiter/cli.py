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


# TODO: Metaclass which defines match statement basd on method tree.
class WikiScriptEngine:
    def __init__(self):
        self.functions = {}

    def cmd_func_init(self, name):
        function = []
        line = None
        while True:
            line = input(">>> ")
            if line == 'end':
                break

            function.append(line)
            
        self.functions[name] = function
    
    def parse_cmd(self, command):
        raise NotImplementedError("This method must be implemented by a subclass.")

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


class WikiPrompt(WikiScriptEngine):
    def __init__(self, root_dir, crawler, search_precaching=False):
        # TODO: move to app setup
        nltk.download('wordnet')
        nltk.download('omw-1.4')

        self.search_precaching = search_precaching

        self.crawler = crawler
        self.oracle = Oracle(root_dir, self)

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_colloc': None, 'selection': None}
    
    def page_wrapper(self, page):
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    # TODO: Fixed frayed logic, printing should be separate. use parse_page instead.
    def analyze_page_wrapper(self, page, printing=True):
        page['freq'], page['colloc'] = analyze_page(page, printing=printing)
        return self.page_wrapper(page)
        
    def handle_search(self, topic):
        results = list(self.crawler.search(topic, soup=False, precache=self.search_precaching))
        if len(results) == 1:
            self.analyze_page_wrapper(results[0], printing=False)
            self.pointer['selection'] = results[0]['title']

        self.crawl_state['last_search'] = results

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)

            self.analyze_page_wrapper(page)
        else:
            print("Invalid Wikipedia url.")
    
    def conditional_idx_selector(self, idx):
        # Redundant condition with select_result. TODO: Clean up frayed logic paths. Refactor to fully cover.
        # TODO: generalize better. lol. self.pointer['selection']
        if len(idx) >= 1:
            try:
                page = select_result(self.crawl_state['last_search'], self.search_precaching, int(idx[0]))
            except ValueError:
                page = select_result(self.crawl_state['last_search'], self.search_precaching)
        else:
            page = select_result(self.crawl_state['last_search'], self.search_precaching, -1)
        
        return page

    def handle_state(self, subcmd):
        try:
            state = self.crawl_state['pages'][self.crawl_state['page_stack'][-1]]
        except IndexError:
            state = None

        try:
            match subcmd:
                case ['colloc', *phrase]:
                    if len(phrase) == 0:
                        print_results(state['colloc'], True)
                    else:
                        phrase = " ".join(phrase)

                        most_similar = (0.0, None)
                        for colloc in state['colloc']:
                            colloc = " ".join(colloc)
                            similarity = jaro_winkler_similarity(colloc, phrase) 
                            # logging.debug(f"{colloc} == {phrase}: {similarity}")

                            if similarity > most_similar[0]:
                                most_similar = (similarity, colloc)

                        self.pointer['most_similar_colloc'] = most_similar[1]
                        print(f"Most similar collocation: {most_similar[1]}")

                case ['sa', *idx]:
                    try:
                        idx = int(idx[0])
                        selection = list(state['see_also'].values())[idx]

                        page = self.crawler.retrieve(selection)
                        self.analyze_page_wrapper(page)

                    except (ValueError, TypeError) as e:
                        logging.exception("Issue with see also page analysis, just an index error?", exc_info=e)
                        print_results(state['see_also'].keys(), True)

                case ['links', *idx]:
                    if len(idx) == 1:
                        try:
                            idx = int(idx[0])
                            print_results(state['paragraph_links'][idx].keys(), True)
                        except ValueError:
                            pass
                    else:
                        for idx, para in enumerate(state['paragraph_links']):
                            print(f"---/t{idx}/t---")
                            print_results([f"\t{key}" for key in para.keys()], True)
                case ['getlink', pgidx, idx]:
                    try:
                        pgidx = int(pgidx)
                        idx = int(idx)
                        
                        page = select_result(state['paragraph_links'][pgidx].keys(), self.search_precaching, idx)
                        self.analyze_page_wrapper(page)
                    except ValueError:
                        print("Invalid indices to paragraph link.")

                case ['list', *idx]:
                    if len(idx) == 0:
                        print_results(self.crawl_state['pages'].keys(), True)
                    else:
                        try:
                            idx = int(idx[0])
                            state = self.crawl_state['pages'][self.crawl_state['page_stack'][idx]]
                            self.analyze_page_wrapper(state)
                        except ValueError:
                            pass
                        
                case ['res', *idx]:
                    if len(idx) == 0:
                        print_results(self.crawl_state['last_search'], self.search_precaching)
                    else:
                        if len(self.crawl_state['last_search']) == 1:
                            page = self.crawl_state['last_search'][0]
                        # Redundant condition with select_result. TODO: Clean up frayed logic paths.
                        elif len(idx) >= 1:
                            page = self.conditional_idx_selector(idx)

                        self.analyze_page_wrapper(page)
                        self.crawl_state['user_choice_stack'].append(page['title'])

                case ['pop']:
                    self.pointer['selection'] = self.crawl_state['page_stack'].pop()
                    self.crawl_state['pop_stack'].append(self.pointer['selection'])
                case ['unpop']:
                    self.crawl_state['page_stack'].append(self.crawl_state['pop_stack'].pop())
                case ['show']:
                    try:
                        analyze_page(self.crawl_state['pages'][self.pointer['selection']])
                    except KeyError:
                        print("No selection to show.")

                case _:
                    pass
        except (ValueError, IndexError) as e:
            logging.exception("Handle_state choice error.", exc_info=e)

    def handle_colloc_move(self, jump_phrase):
        self.run_script(f"st colloc {jump_phrase}",
                        f"s {self.pointer['most_similar_colloc']}",
                         "st sel 0")

    def handle_freq_move(self, jump_phrase):
        pass

    def parse_cmd(self, command):
        match command.split():
            case ['s', *phrase]: 
                if len(phrase) == 0:
                    return

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

            case ['newf', name]:
                self.handle_write_func(name)

            case _: 
                print(f"Unknown command: {command}")


