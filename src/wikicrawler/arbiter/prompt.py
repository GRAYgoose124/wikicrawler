import logging

import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import jaro_winkler_similarity

from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import print_sentiment

from .oracle import Oracle
from .utils.search import print_results

from .script import WikiScriptEngine
from .seer import Seer


logger = logging.getLogger(__name__)


class WikiPrompt(WikiScriptEngine):
    def __init__(self, config, crawler, cacher=None):
        super().__init__(config, crawler, cacher=cacher)

        self.oracle = Oracle(self, cacher=cacher)
        self.seer = Seer(self, cacher=cacher)
    
    def handle_search(self, topic, interactive=True):
        if topic == 'most_similar_colloc':
            topic = self.pointer['most_similar_colloc']
        elif topic == 'most_similar_freq':
            topic = self.pointer['most_similar_freq']

        logger.debug(f"Search: {topic}")

        results = list(self.crawler.search(topic, precache=self.search_precaching))

        if len(results) == 1:
            self.analyze_page_wrapper(results[0][1], printing=interactive)

        self.crawl_state['last_search'] = results

    def handle_url(self, url):
        if WikiCrawler.wiki_regex.match(url):
            page = self.crawler.retrieve(url)

            self.analyze_page_wrapper(page)
        else:
            print("Invalid Wikipedia url.")
    
    # handle_state
    def handle_state_colloc(self, state, phrase):
        # st colloc
        if len(phrase) == 0:
            print_results(state['stats']['collocations'])
        # st colloc <phrase>
        else:
            phrase = " ".join(phrase)

            most_similar = (0.0, None)
            for colloc in state['stats']['collocations']:
                colloc = "".join(colloc)
                similarity = jaro_winkler_similarity(colloc, phrase) 

                if similarity > most_similar[0]:
                    most_similar = (similarity, colloc)

            self.pointer['most_similar_colloc'] = most_similar[1]
            logger.debug(f"Most similar collocation: {most_similar[1]}")

    def handle_state_freq(self, state, phrase):
        # st freq
        if len(phrase) == 0:
            print_results(state['stats']['frequencies'])
        # st freq <phrase>
        else:
            phrase = " ".join(phrase)

            most_similar = (0.0, None)
            for freq in state['stats']['frequencies']:
                freq = "".join(freq)
                similarity = jaro_winkler_similarity(freq, phrase) 

                if similarity > most_similar[0]:
                    most_similar = (similarity, freq)

            self.pointer['most_similar_freq'] = most_similar[1]
            logger.debug(f"Most similar frequency: {most_similar[1]}")

    def handle_state_seealso(self, state, idx):
        # st sa <idx>
        try:
            idx = int(idx[0])
            selection = list(state['see_also'].values())[idx]

            page = self.crawler.retrieve(selection)
            self.analyze_page_wrapper(page)
        # st sa
        except (ValueError, TypeError, IndexError) as e:
            print_results(list(state['see_also'].keys()))

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

            page = self.crawler.retrieve(selection)

            self.analyze_page_wrapper(page)
        # st links <idx> - equivalent to st links -1 <idx>
        elif len(idx) == 1:
            try:
                idx = int(idx[0])
                print_results(list(state['paragraph_links'][idx].keys()))
            except ValueError:
                logger.debug("Invalid index to paragraph link. Did you enter a number?")
        # st links - list
        else:
            try:
                for idx, para in enumerate(state['paragraph_links']):
                    print(f"---\t{idx}\t---")
                    if len(para) == 0:
                        continue
                    print_results(list(para.keys()))
            except TypeError as e:
                logger.debug(f'No paragraph links found. Is state set? {state}', exc_info=e)

    def handle_state_hist(self, state, idx):
        # st list
        if len(idx) == 0:
            print_results(list(self.crawl_state['pages'].keys()))
        # st list <idx>
        else:
            try:
                idx = int(idx[0])
                state = self.crawl_state['pages'][self.crawl_state['page_stack'][idx]]

                self.analyze_page_wrapper(state, printing=False)
            except ValueError as e:
                logger.debug("Invalid index to page list.", exc_info=e)
                        
    def handle_state_found(self, state, idx):
        # st found
        if self.crawl_state['last_search'] is None:
            return

        if len(idx) == 0:
            if isinstance(self.crawl_state['last_search'], dict):
                last_search = list(self.crawl_state['last_search'].keys())
            else:
                last_search = self.crawl_state['last_search']

            print_results(last_search)
        # st res <idx>
        else:
            if len(self.crawl_state['last_search']) == 1:
                page = self.crawl_state['last_search'][0]
            elif len(idx) >= 1:
                page = self.crawl_state['last_search'][int(idx[0])]
        
            self.analyze_page_wrapper(page)

    def handle_state(self, subcmd):
        """
        Handle state commands.
        
        st colloc <phrase> - get most similar collocation
        st colloc - list collocations
        
        st freq <phrase> - get most similar frequency
        st freq - list frequencies

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
        st current - show current page title

        st sentences <start> <end> - analyze current page with sentences from <start> to <end>
        
        st save - save current page to file
        st delete - delete current page from file

        st help - print this message
        """
        try:
            state = self.crawl_state['pages'][self.pointer['selection']]
        except (IndexError, KeyError):
            logger.debug("No page selected.")
            return

        try:
            match subcmd:
                case ['colloc', *phrase]:
                    self.handle_state_colloc(state, phrase)
                case ['freq', *phrase]:
                    self.handle_state_freq(state, phrase)

                case ['sa', *idx]:
                    self.handle_state_seealso(state, idx)
                case ['links', *idx]:
                    self.handle_state_links(state, idx)
                case ['hist', *idx]:
                    self.handle_state_hist(state, idx)
                case ['found', *idx]:
                    self.handle_state_found(state, idx)

                case ['pop']:
                    self.pointer['selection'] = self.crawl_state['page_stack'].pop()
                    self.crawl_state['pop_stack'].append(self.pointer['selection'])
                case ['unpop']:
                    self.crawl_state['page_stack'].append(self.crawl_state['pop_stack'].pop())

                case ['current']:
                    print(self.pointer['selection'])
                case ['show', *amount]:
                    try:
                        try:
                            amount = float(amount[0])
                        except (IndexError, ValueError):
                            amount = .05
                
                        self.analyze_page_wrapper(self.crawl_state['pages'][self.pointer['selection']], amount=amount, printing=True)
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
                    return False
            return True
        except (ValueError, IndexError) as e:
            logging.exception("Handle_state choice error.", exc_info=e)


    def parse_cmd(self, command, interactive=False):
        """
        Parse command and execute.

        s <phrase> - search for phrase
        s most_similar_colloc - get most similar collocation
        s most_similar_freq - get most similar collocation

        u <url> - search for url
        
        st <subcmd> - handle state commands
        o[racle] <subcmd> - handle oracle commands
        seer <subcmd> - handle seer commands

        pointer - print pointer
        state - print state

        newf <name> - create new function

        help - print help
        exit - exit cli
        """
        match command.split():
            case ['s', *phrase]: 
                if len(phrase) != 0:
                    self.handle_search(" ".join(phrase), interactive=interactive)

            case ['u', url]:
                self.handle_url(url)

            case ['st', *subcmd]:
                self.handle_state(subcmd)

            case ['o' | 'oracle', *cmd]:
                self.oracle.parse_cmd(cmd)

            case ['seer', *cmd]:
                self.seer.parse_cmd(cmd)

            case ['pointer']:
                print(self.pointer)
            case ['state']:
                print(self.crawl_state)

            case ['help']:
                # TODO: Read from source.
                print(self.parse_cmd.__doc__, sep='\n')
            case ['exit']:
                print("Goodbye!")

            case ['newf', name]:
                self.cmd_func_init(name)

            case _: 
                print(f"Unknown command: {command}")
                return False
        return True
