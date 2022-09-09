import logging

import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import jaro_winkler_similarity

from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import analyze_page

from .oracle import Oracle
from .utils.other import help_msg
from .utils.search import print_results, select_result
from .script import WikiScriptEngine


logger = logging.getLogger(__name__)


class WikiPrompt(WikiScriptEngine):
    def __init__(self, root_dir, crawler, search_precaching=False):
        super().__init__()
        # TODO: move to app setup
        nltk.download('wordnet')
        nltk.download('omw-1.4')

        self.search_precaching = search_precaching

        self.crawler = crawler
        self.oracle = Oracle(root_dir, self)
    
    def page_wrapper(self, page):
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    # TODO: Fixed frayed logic, printing should be separate. use parse_page instead.
    def analyze_page_wrapper(self, page, printing=True):
        page['freq'], page['colloc'] = analyze_page(page, printing=printing)
        return self.page_wrapper(page)
        
    def handle_search(self, topic):
        if topic == 'most_similar_colloc':
            topic = self.pointer['most_similar_colloc']

        logging.debug(f"Search: {topic}")

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
                    # st colloc
                    if len(phrase) == 0:
                        print_results(state['colloc'], True)
                    # st colloc <phrase>
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
                    # st sa <idx>
                    try:
                        idx = int(idx[0])
                        selection = list(state['see_also'].values())[idx]

                        page = self.crawler.retrieve(selection)
                        self.analyze_page_wrapper(page)
                    # st sa
                    except (ValueError, TypeError) as e:
                        print_results(state['see_also'].keys(), True)

                case ['links', *idx]:
                    # st links <pgidx> <idx> - get
                    if len(idx) >= 2:
                        try:
                            pgidx = int(idx[0])
                            idx = int(idx[1])
                        except ValueError:
                            print("Invalid indices to paragraph link.")    
                            print(list(state['paragraph_links'][pgidx].values()))
                            return

                        selection = list(state['paragraph_links'][pgidx].values())[idx]

                        page = self.crawler.retrieve("https://en.wikipedia.org" + selection)

                        self.analyze_page_wrapper(page)
                    # st links <idx> - equivalent to st links -1 <idx>
                    elif len(idx) == 1:
                        try:
                            idx = int(idx[0])
                            print_results(state['paragraph_links'][idx].keys(), True)
                        except ValueError:
                            pass
                    # st links - list
                    else:
                        for idx, para in enumerate(state['paragraph_links']):
                            print(f"---\t{idx}\t---")
                            print_results([f"\t{key}" for key in para.keys()], True)

    
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
                        elif len(idx) >= 1:
                            page = self.conditional_idx_selector(idx)

                        self.analyze_page_wrapper(page)
                        self.pointer['selection'] = page['title']
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
                        f"s most_similar_colloc",
                        "st res 0")

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
                # TODO: Read from source.
                print(*help_msg, sep='\n')
            case ['exit']:
                pass

            case ['p_colloc']:
                print("Colloc:", self.pointer['most_similar_colloc'])

            case ['newf', name]:
                self.handle_write_func(name)

            case _: 
                print(f"Unknown command: {command}")