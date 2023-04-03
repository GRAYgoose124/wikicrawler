import logging

import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import jaro_winkler_similarity



from ..core.crawler import WikiCrawler
from ..core.sentiment.paragraph import print_sentiment # TODO: Substitute with textual compatible version.

from .oracle import Oracle
from .utils.search import print_results

from .script import WikiScriptEngine
from .utils.console import console
from .seer import Seer


class WikiPrompt(WikiScriptEngine):
    def __init__(self, config, crawler, cacher=None, parent_logger=None):
        super().__init__(config, crawler, cacher=cacher, parent_logger=parent_logger)

        self.oracle = Oracle(self, cacher=cacher, parent_logger=parent_logger)
        self.seer = Seer(self, cacher=cacher, parent_logger=parent_logger)

        self.commands = {}
    
    def handle_search(self, topic, interactive=True):
        """ Search for a topic and update the crawl state.

        Args:
            topic (str): The topic to search for.
            interactive (bool): Whether being called from interactive mode or by a script.
                                    This controls printing behaviour.
        """
        # TODO: generalize this for all commands.
        if topic == 'most_similar_colloc':
            topic = self.pointer['most_similar_colloc']
        elif topic == 'most_similar_freq':
            topic = self.pointer['most_similar_freq']

        self.logger.debug(f"Search: {topic}")

        results = list(self.crawler.search(topic, precache=self.search_precaching))

        if len(results) == 1:
            self.analyze_page_wrapper(results[0][1], printing=interactive)

        self.crawl_state['last_search'] = results
        return results

    def handle_url(self, urls):
        """ Retrieve a page from a URL and update the crawl state.

        Args:
            url (str): The URL to retrieve.
        """
        for url in urls:
            if WikiCrawler.wiki_regex.match(url):
                # TODO: Does this need a rate limit?
                page = self.crawler.retrieve(url)

                return self.analyze_page_wrapper(page, printing=False)
            else:
                print("Invalid Wikipedia url.")
    
    # handle_state
    def handle_state_colloc(self, state, phrase):
        """ Handle the state command for finding collocations, in particular, it sets the most_similar_colloc pointer.
        
        Args:
            state (dict): The crawl state operated on. NOTE: We are passing this to make sure the 
                                                state is properly updated for the script engine. Fix?
            phrase (list): The phrase to find the most similar collocation for.
        """
        # st colloc
        if len(phrase) == 0:
            return [" ".join(x) for x in state['stats']['collocations']] # TODO: used to use print_results, mimic that behaviour.
        # st colloc <phrase>
        else:
            phrase = " ".join(phrase)

            most_similar = (0.0, "")
            for colloc in state['stats']['collocations']:
                colloc = " ".join(colloc)
                similarity = jaro_winkler_similarity(colloc, phrase) 

                if similarity > most_similar[0]:
                    most_similar = (similarity, colloc)

            self.pointer['most_similar_colloc'] = most_similar[1]
            self.logger.debug(f"Most similar collocation: {most_similar[1]}")
            return most_similar[1]

    def handle_state_freq(self, state, phrase):
        """ Handle the state command for finding most similar frequent phrases, in particular, it sets XAthe most_similar_freq pointer.
        
        Args:
            state (dict): The crawl state operated on.
            phrase (list): The phrase to find the most similar frequent phrase for.
        """
        # st freq
        if len(phrase) == 0:
            return state['stats']['frequencies'] # TODO: used to use print_results, mimic that behaviour.
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
            self.logger.debug(f"Most similar frequency: {most_similar[1]}")
            return most_similar[1]

    def handle_state_seealso(self, state, idx):
        """ Handle the state command for see also links.
        
        Args:
            state (dict): The crawl state operated on.
            idx (list): The index to the see also link, if neglected print all results."""
        # st sa <idx>
        try:
            idx = int(idx[0])
            selection = list(state['see_also'].values())[idx]

            page = self.crawler.retrieve(selection)
            return self.analyze_page_wrapper(page)
        # st sa
        except (ValueError, TypeError, IndexError) as e:
            return list(state['see_also'].keys())  # TODO: used to use print_results, mimic that behaviour.

    def handle_state_links(self, state, idx):
        """ Handle the state command for getting and viewing links.

        Args:
            state (dict): The crawl state operated on.
            idx (list): The index to the link, if neglected print all results.
        """
        # st links <pgidx> <idx> - get
        if len(idx) >= 2:
            try:
                pgidx = int(idx[0])
                idx = int(idx[1])
            except ValueError:
                self.logger.error("Invalid indices to paragraph link.")    
                self.logger.debug(list(state['paragraph_links'][pgidx].values()))
                return

            selection = list(state['paragraph_links'][pgidx].values())[idx]

            page = self.crawler.retrieve(selection)

            return self.analyze_page_wrapper(page) # TODO: handle analyze_page_wrapper
        # st links <idx> - equivalent to st links -1 <idx>
        elif len(idx) == 1:
            try:
                idx = int(idx[0])
                return list(state['paragraph_links'][idx].keys()) # TODO: used to use print_results, mimic that behaviour.
            except ValueError:
                self.logger.debug("Invalid index to paragraph link. Did you enter a number?")
        # st links - list
        else:
            try:
                for idx, para in enumerate(state['paragraph_links']):
                    if len(para) == 0:
                        continue
                    return idx, list(para.keys()) # TODO: used to use print_results, mimic that behaviour.
            except TypeError as e:
                self.logger.debug(f'No paragraph links found. Is state set? {state}', exc_info=e)

    def handle_state_hist(self, state, idx):
        """ Handle the state command for getting and viewing history of page traversal.

        Args:
            state (dict): The crawl state operated on.
            idx (list): The index to the history, if neglected print all results.
    """
        # st list
        if len(idx) == 0:
            return list(self.crawl_state['pages'].keys()) # TODO: used to use print_results, mimic that behaviour.
        # st list <idx>
        else:
            try:
                state = self.crawl_state['pages'][list(self.crawl_state['pages'].keys())[int(idx[0])]]

                return self.analyze_page_wrapper(state, printing=False) # TODO: handle analyze_page_wrapper
            except ValueError as e:
                self.logger.debug("Invalid index to page list.", exc_info=e)
                        
    def handle_state_found(self, state, idx):
        """ Handle the state command for getting and viewing found pages during searches.

        Args:
            state (dict): The crawl state operated on.
            idx (list): The index to the found page, if neglected print all results.
        """
        # st found
        if self.crawl_state['last_search'] is None:
            return

        if len(idx) == 0:
            if isinstance(self.crawl_state['last_search'], dict):
                last_search = list(self.crawl_state['last_search'].keys())
            else:
                last_search = self.crawl_state['last_search']

            return last_search  # TODO: used to use print_results, mimic that behaviour.
        # st found <idx>
        else:
            if len(self.crawl_state['last_search']) == 1:
                page = self.crawl_state['last_search'][0]
            elif len(idx) >= 1:
                try:
                    page = self.crawl_state['last_search'][int(idx[0])]
                except IndexError as e:
                    # TODO/FIX: Somehow when cmoving from autosearch, the idx can be out of range.
                    # I believe this is when there are no search results.
                    self.logger.exception(f"Invalid index to found page. {idx[0]}, {len(self.crawl_state['last_search'])}", exc_info=e)
                    return

            # TODO: Consolidate, frayed logic consequence?
            if isinstance(page, tuple):
                page = page[1]
        
            return self.analyze_page_wrapper(page)  # TODO: handle analyze_page_wrapper

    def handle_state(self, subcmd):
        """
        Handle state commands. 
        State commands are commands that operate on the current crawl state.
        
        Help List:
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

            st sents <start> <end> - analyze current page with sentences from <start> to <end>
            
            st save - save current page to file
            st delete - delete current page from file

            st help - print this message
        """
        try:
            state = self.crawl_state['pages'][self.pointer['selection']]
        except (IndexError, KeyError):
            self.logger.debug("No page selected.")
            return

        try:
            match subcmd:
                case ['colloc', *phrase]:
                    return self.handle_state_colloc(state, phrase)
                case ['freq', *phrase]:
                    return self.handle_state_freq(state, phrase)

                case ['sa', *idx]:
                    return self.handle_state_seealso(state, idx)
                case ['links', *idx]:
                    return self.handle_state_links(state, idx)
                case ['hist', *idx]:
                    return self.handle_state_hist(state, idx)
                case ['found', *idx]:
                    return self.handle_state_found(state, idx)

                case ['pop']:
                    self.pointer['selection'] = self.crawl_state['page_stack'].pop()
                    self.crawl_state['pop_stack'].append(self.pointer['selection'])
                case ['unpop']:
                    self.crawl_state['page_stack'].append(self.crawl_state['pop_stack'].pop())

                case ['current']:
                    return self.pointer['selection']
                case ['show', *amount]:
                    try:
                        try:
                            if len(amount) == 1:
                                amount = amount[0]
                                amount = float(amount)
                            else:
                                amount = .1

                        except (IndexError, ValueError):
                            amount = .1
                
                        return self.analyze_page_wrapper(self.crawl_state['pages'][self.pointer['selection']], amount=amount, printing=True)
                    except KeyError:
                        return "No selection to show."

                case ['sents', *_start_stop]:
                    # parse start and stop - `st sents [start|'-'|None] [stop|'-'|None]`
                    try:
                        start, stop = _start_stop
                    except ValueError:
                        if len(_start_stop) == 1:
                            start, stop = _start_stop[0], None
                        else:
                            start, stop = None, None

                    # store the last start and stop
                    if start is not None and start != '-':
                        self._sentences_start = start
                    if stop is not None and stop != '-':
                        self._sentences_stop = stop

                    # replace with last start and stop if not specified
                    if start is None or start == '-':
                        start = self._sentences_start
                    if stop is None or stop == '-':
                        stop = self._sentences_stop

                    paragraphs = "".join(self.crawl_state['pages'][self.pointer['selection']]['paragraphs'])
                    sentences = nltk.sent_tokenize(paragraphs)

                    self.pointer['selected_text'] = sentences[int(start):int(stop)]
                    return self.pointer['selected_text']  # TODO: used to use print_sentiment, mimic that behaviour.
                
                case ['save']:
                    return self.save_state()
                case ['del']:
                    return self.del_state()

                case ['help']:
                    return self.handle_state.__doc__

                case _:
                    return False
            return True
        except (ValueError, IndexError) as e:
            self.logger.exception("Handle_state choice error.", exc_info=e)


    def parse_cmd(self, command, interactive=False):
        """
        Parse basic command and execute. 

        Help List:
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
        self.logger.debug(command)

        match command.split():
            case ['s', *phrase]: 
                if len(phrase) != 0:
                    return self.handle_search(" ".join(phrase), interactive=interactive)

            case ['u', *url]:
                return self.handle_url(url)

            case ['st', *subcmd]:
                return self.handle_state(subcmd)

            case ['o' | 'oracle', *cmd]:
                return self.oracle.parse_cmd(cmd)

            case ['seer', *cmd]:
                self.seer.parse_cmd(cmd)

            case ['pointer']:
                return self.pointer
            case ['state']:
                return self.crawl_state

            case ['help']:
                # TODO: Read from source.
                return self.parse_cmd.__doc__
            case ['newf', name]:
                return self.cmd_func_init(name)

            case _: 
                return f"Unknown command: {command}"
