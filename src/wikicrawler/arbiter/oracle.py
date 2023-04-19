import logging
import os
from random import randint

from .utils.frequency import get_highest_freq



class Oracle:
    """ TODO: Wrapper class and refactor oracle into sub-module.

    Oracle is an extension class for the prompt that provides 
    a higher level of abstraction for the user. It is meant to
    be a tool for the user to use to navigate the wiki graph
    and to provide a more natural language interface for the
    user to interact with the crawler.
    """
    def __init__(self, prompt, cacher=None, parent_logger=None):
        self.logger = parent_logger.getChild(__name__) if parent_logger is not None else logging.getLogger(__name__)
        self.prompt = prompt

        if cacher is not None:
            cacher.register_hook(self.save_state)

        oracle_path = self.prompt.root_dir + "/oracle"
        self.oracle_dir = oracle_path

        if not os.path.exists(oracle_path):
            os.makedirs(oracle_path)

        self.brain = None

    def save_state(self):
        pass

    def handle_autosearch(self, start, n, hook=None):
        """ Allows you to search through a list of pages from just a start query.
        
        It traverses by the highest frequency word's most similar collocation.
        You can also have it optionally call a script command as a hook on every iteration.

        TODO: Work on script engine to allow for async execution.
        TODO: fix pointer to make it more intuitive.
        """
        saved_pointer = self.prompt.pointer.copy()

        script = [f"s {start}", 
                   "st found 0", 
                   "seer build"]

        for _ in range(n-1):
            # TODO: At time of script "compile", this is not properly set, of course.
            # Probably should wrap it in a lambda and make the script engine evaluate it.
            cmov = lambda: "o cmov {} {}".format(randint(0, len(self.prompt.crawl_state['last_search'])-1), 
                                                 get_highest_freq(self.prompt.crawl_state['pages']\
                                                                [self.prompt.pointer['selection']]\
                                                                    ['stats']['frequencies']))

            script.append(cmov)
            if hook is not None:
                # TODO: make hook a list?
                script.append(f"{hook}")
        
        ## logging.debug("Running script:\n\t{}".format('\n\t'.join(script))) TODO: DelayedExecution lambda wrapper?
        self.prompt.run_script(script)

        return self.prompt.crawl_state['pages'][self.prompt.pointer['selection']]

    def handle_freq_move(self, n, jump_phrase):
        """
        Move to the first page that matches the nth most common frequency of the current page.
        """
        self.prompt.run_script([f"st freq {jump_phrase}",
                                 "s most_similar_freq",
                                f"st found {n}"])

        # logger.debug(f"fmov proc: {jump_phrase}, {self.prompt.pointer['most_similar_freq']}, {self.prompt.crawl_state['last_search'][0]}")
        return self.prompt.crawl_state['pages'][self.prompt.pointer['selection']]

    # TODO: refactor into file.
    def handle_colloc_move(self, n, jump_phrase):
        """
        Move to the first page that matches the nth most common collocation of the current page.
        """
        self.prompt.run_script([f"st colloc {jump_phrase}",
                                 "s most_similar_colloc",
                                f"st found {n}"])

        return self.prompt.crawl_state['pages'][self.prompt.pointer['selection']]
        # logger.debug(f"cmov proc: {jump_phrase}, {self.prompt.pointer['most_similar_colloc']}, {self.prompt.crawl_state['last_search'][0]}")

    # TODO: Oracle should compile a summarization of the crawl and user input.
    def parse_cmd(self, command):
        """
        Parse the command and return the function and arguments.
        
        This is called by the prompt's parse_cmd function as a sub-parser.

        Help:
            div - divine traversal state

            as  <n> <start> - auto search through n pages from start query.
            bas <n> <start> - auto search through n pages from start query, and build them with the Seer.

            cmov <n> <phrase> - move to first page matched by phrase==collocations[n] of current page.
            fmov <n> <phrase> - move to first page matched by phrase==frequency[n] of current page.

            help - show help
        """
        match command:
            case ['div']:
                self.logger.debug('div proc')

            case ['as', n, *start_phrase]:
                try:
                    return self.handle_autosearch(' '.join(start_phrase), int(n))
                except ValueError:
                    self.logger.info("Invalid arguments for as command.")

            case ['bas', n, *start_phrase]:
                try:
                    return self.handle_autosearch(' '.join(start_phrase), int(n), hook="seer build")
                except ValueError:
                    self.logger.info("Invalid arguments for bas command.")

            case ['cmov', n, *jump_phrase]:
                try:
                    return self.handle_colloc_move(int(n), " ".join(jump_phrase))
                except ValueError:
                    self.logger.info("Invalid jump phrase or n")

            case ['fmov', n, *jump_phrase]:
                try:
                    return self.handle_freq_move(int(n), " ".join(jump_phrase))
                except ValueError:
                    self.logger.info("Invalid jump phrase or n")


            case ['help']:
                return self.parse_cmd.__doc__
