import logging

import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import jaro_winkler_similarity

from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import analyze_page, print_sentiment

from .oracle import Oracle
from .utils.other import help_msg
from .utils.search import print_results, select_result

from .script import WikiScriptEngine


logger = logging.getLogger(__name__)


class WikiPrompt(WikiScriptEngine):
    def __init__(self, root_dir, crawler, search_precaching=False, cacher=None):
        super().__init__(root_dir, search_precaching=search_precaching, cacher=cacher)

        self.crawler = crawler

        self.oracle = Oracle(self)
    
    def handle_search(self, topic, interactive=True):
        if topic == 'most_similar_colloc':
            topic = self.pointer['most_similar_colloc']

        logging.debug(f"Search: {topic}")

        results = list(self.crawler.search(topic, soup=False, precache=self.search_precaching))

        if len(results) == 1:
            self.analyze_page_wrapper(results[0], printing=interactive)
            self.pointer['selection'] = results[0]['title']

        self.crawl_state['last_search'] = results

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)

            self.analyze_page_wrapper(page)
        else:
            print("Invalid Wikipedia url.")
    
    def handle_freq_move(self, jump_phrase):
        pass

    # handle_state
    def handle_state_colloc(self, state, phrase):
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

    def handle_state_seealso(self, state, idx):
        # st sa <idx>
        try:
            idx = int(idx[0])
            selection = list(state['see_also'].values())[idx]

            page = self.crawler.retrieve(selection)
            self.analyze_page_wrapper(page)
        # st sa
        except (ValueError, TypeError, IndexError) as e:
            print_results(state['see_also'].keys(), True)

    def handle_state_links(self, state, idx):
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
                logging.debug("Invalid index to paragraph link. Did you enter a number?")
        # st links - list
        else:
            try:
                for idx, para in enumerate(state['paragraph_links']):
                    print(f"---\t{idx}\t---")
                    print_results([f"\t{key}" for key in para.keys()], True)
            except TypeError:
                logging.debug('No paragraph links found. Is state set?')

    def handle_state_list(self, state, idx):
        # st list
        if len(idx) == 0:
            print_results(self.crawl_state['pages'].keys(), True)
        # st list <idx>
        else:
            try:
                idx = int(idx[0])
                state = self.crawl_state['pages'][self.crawl_state['page_stack'][idx]]
                self.analyze_page_wrapper(state)
            except ValueError:
                pass
                        
    def handle_state_res(self, state, idx):
        # st res
        if len(idx) == 0:
            print_results(self.crawl_state['last_search'], self.search_precaching)
        # st res <idx>
        else:            
            if len(self.crawl_state['last_search']) == 1:
                page = self.crawl_state['last_search'][0]
            elif len(idx) >= 1:
                page = self.crawl_state['last_search'][int(idx[0])]
                if isinstance(page, str):
                    page = self.crawler.retrieve(page)
                else:
                    page = self.conditional_idx_selector(idx)

            self.analyze_page_wrapper(page)
            self.crawl_state['user_choice_stack'].append(page['title'])

    def handle_state(self, subcmd):
        """
        Handle state commands.
        
        st colloc <phrase> - get most similar collocation
        st colloc - list collocations
        
        st sa <idx> - get see also page
        st sa - list see also pages
        
        st links <pgidx> <idx> - get paragraph link
        st links <idx> - list paragraph links
        st links - list all paragraph links
        
        st hist <idx> - get page from list
        st hist - list pages
        
        st found <idx> - get page from last search
        st found - list last search
        
        st pop - pop page from stack
        st unpop - unpop page from stack

        st show - analyze current page
        st show <amount> - analyze current page with <amount> of page. (float for percentage, int for number of sentences)

        st sentences <start> <end> - analyze current page with sentences from <start> to <end>
        
        st most_similar_colloc - get most similar collocation

        st save - save current page to file
        st delete - delete current page from file

        st help - print this message
        """
        try:
            state = self.crawl_state['pages'][self.crawl_state['page_stack'][-1]]
        except IndexError:
            state = None

        try:
            match subcmd:
                case ['colloc', *phrase]:
                    self.handle_state_colloc(state, phrase)

                case ['sa', *idx]:
                    self.handle_state_seealso(state, idx)
                case ['links', *idx]:
                    self.handle_state_links(state, idx)
                case ['hist', *idx]:
                    self.handle_state_list(state, idx)
                case ['found', *idx]:
                    self.handle_state_res(state, idx)

                case ['pop']:
                    self.pointer['selection'] = self.crawl_state['page_stack'].pop()
                    self.crawl_state['pop_stack'].append(self.pointer['selection'])
                case ['unpop']:
                    self.crawl_state['page_stack'].append(self.crawl_state['pop_stack'].pop())
                case ['show', *amount]:
                    try:
                        try:
                            amount = float(amount[0])
                        except (IndexError, ValueError):
                            amount = 1.0

                        analyze_page(self.crawl_state['pages'][self.pointer['selection']], amount=amount)
                    except KeyError:
                        print("No selection to show.")

                case ['sentences', start, stop]:
                    paragraphs = "".join(self.crawl_state['pages'][self.pointer['selection']]['paragraphs'])
                    sentences = nltk.sent_tokenize(paragraphs)

                    self.pointer['selected_text'] = sentences[int(start):int(stop)]
                    print_sentiment(self.pointer['selected_text'])
                
                case ['save']:
                    self.save_state()
                case ['del']:
                    self.del_state()

                case ['help']:
                    print(self.handle_state.__doc__)

                case _:
                    pass
        except (ValueError, IndexError) as e:
            logging.exception("Handle_state choice error.", exc_info=e)

    def parse_cmd(self, command, interactive=False):
        """
        Parse command and execute.

        s <phrase> - search for phrase
        u <url> - search for url
        
        st <subcmd> - handle state commands
        ora <subcmd> - handle oracle commands


        pointer - print pointer
        state - print state

        newf <name> - create new function

        help - print help
        exit - exit cli
        """
        match command.split():
            case ['s', *phrase]: 
                if len(phrase) == 0:
                    return

                self.handle_search(" ".join(phrase), interactive=interactive)

            case ['u', url]:
                self.handle_url(url)

            case ['st', *subcmd]:
                self.handle_state(subcmd)


            case ['ora', *cmd]:
                self.oracle.parse_cmd(cmd)

            case ['pointer']:
                print(self.pointer)
            case ['state']:
                print(self.crawl_state)

            case ['help']:
                # TODO: Read from source.
                print(self.parse_cmd.__doc__, sep='\n')
            case ['exit']:
                pass

            case ['newf', name]:
                self.cmd_func_init(name)

            case _: 
                print(f"Unknown command: {command}")