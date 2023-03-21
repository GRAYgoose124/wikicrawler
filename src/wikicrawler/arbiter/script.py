from functools import partial
import json
import logging
import os
# For command history
if os.name == 'posix':
    import readline
from io import TextIOWrapper
from typing import Callable

from ..core.sentiment.paragraph import analyze_page


logger = logging.getLogger(__name__)


class WikiScriptEngine:
    def __init__(self, config, crawler, cacher=None):
        self.config = config

        self.crawler = crawler
        self.cacher = cacher
        if cacher is not None:
            cacher.register_hook(self.save_state)

        self.search_precaching = config['search_precaching']

        self.root_dir = config['data_root']
        self.prompt_dir = self.root_dir + '/prompt'
        if not os.path.exists(self.prompt_dir):
            os.makedirs(self.prompt_dir)

        # -- init state from file --

        if config['prompt_state'] is not None:
            filename = config['prompt_state']
        else:
            filename = 'crawl_state'
            config['prompt_state'] = filename

        if os.path.exists(self.prompt_dir + f'/{filename}.json'):
            with open(self.prompt_dir + f"/{filename}.json", 'r') as f:
                self.crawl_state = json.load(f)
        else:
            self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
      
        if config['functions_cache'] is not None:
            filename = config['functions_cache']
        else:
            filename = 'functions_cache'  
            config['functions_cache'] = filename

        if os.path.exists(self.prompt_dir + f'/{filename}.json'):
            with open(self.prompt_dir + f'/{filename}.json', 'r') as f:
                self.functions = json.load(f)
        else:
            self.functions = {}

        if config['pointer_state'] is not None:
            filename = config['pointer_state']
        else:
            filename = 'pointer'

            config['pointer_state'] = filename

        if os.path.exists(self.prompt_dir + f'/{filename}.json'):
            with open(self.prompt_dir + f'/{filename}.json', 'r') as f:
                    self.pointer = json.load(f)
        else:
            self.pointer = { 'most_similar_freq': None, 'most_similar_colloc': None, 'selection': None, 'selected_text': None}
        
    def reset_state(self):
        """ Reset the state of the prompt. 
        """
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_freq': None, 'most_similar_colloc': None, 'selection': None, 'selected_text': None}

    def del_state(self):
        """ Delete the state of the crawler prompt.
        
        This is useful if you want to start over from scratch, removing all the
        pages you've already crawled and the pages you've already selected.
        """
        self.reset_state()

        with open(self.prompt_dir + f"/{self.config['prompt_state']}.json", 'w') as f:
            json.dump(self.crawl_state, f)

        with open(self.prompt_dir + f"/{self.config['pointer_state']}.json", 'w') as f:
            json.dump(self.pointer, f)

    def save_state(self):
        """ Save the state of the prompt.
        """
        try:
            with open(self.prompt_dir + f"/{self.config['prompt_state']}.json", 'w') as f:
                if not hasattr(self, 'crawl_state'):
                    logger.error('crawl_state not defined - crash?')
                    return

                # TODO: make last search just have links in the first place?
                # Removing so partials don't cause a problem. TODO: See above. Need to refactor to remove partials completely.
                #if self.crawl_state['last_search'] is not None and isinstance(self.crawl_state['last_search'][0], tuple):
                self.crawl_state['last_search'] = None
            
                json.dump(self.crawl_state, f, indent=2)
            
            with open(self.prompt_dir + f"/{self.config['functions_cache']}.json", 'w') as f:
                json.dump(self.functions, f, indent=2)

            with open(self.prompt_dir + f"/{self.config['pointer_state']}.json", 'w') as f:
                json.dump(self.pointer, f, indent=2)
        except FileNotFoundError as e:
            logger.debug("Files probably deleted while system was running", exc_info=e)

    def cmd_func_init(self, name, lines=None):
        """ This function is used to initialize a function from script/interactive mode.
        
        It then stores the function in the functions cache.
        """
        function = []
        line = None

        # interactive function define
        if lines is None:
            while True:
                line = input("\t")
                if line == 'end':
                    break

                function.append(line)
        # script function define using lines
        else:
            function = lines

        self.functions[name] = function
    
    def parse_cmd(self, command, interactive=False):
        """ Parse a command from the prompt.
        
        This is a dummy implementation meant to be overridden by subclasses."""
        raise NotImplementedError("This method must be implemented by a subclass.")

    def loop(self):
        """ The main loop of the prompt.
        """
        command = ""

        while command != "exit":
            command = input("> ")
            
            self.parse_cmd(command, interactive=True)

    # TODO: standardize interface
    def run_script(self, script_or_path):
        """ Run a script from a file, string, or list of commands.

        Args:
            script_or_path (TextIOWrapper, str or list): The script to run.
        """
        if isinstance(script_or_path, str):
            # script string
            if '\n' in script_or_path:
                for command in script_or_path.split('\n'):
                    self.parse_cmd(command)
            # script file
            else:
                with open(script_or_path, 'r') as f:
                    for command in f.readlines():
                        self.parse_cmd(command)
        elif isinstance(script_or_path, TextIOWrapper):
            for command in script_or_path:
                self.parse_cmd(command)
        # list of commands
        elif isinstance(script_or_path, list):
            for command in script_or_path:
                # command is a lambda to delay execution until now.
                if isinstance(command, Callable):
                    logger.debug("Running delayed command: {}".format(command))
                    command = command()
                    logger.debug("Command: {}".format(command))

                self.parse_cmd(command)

    # helpers
    def page_wrapper(self, page):
        """ Simple wrapper to make command creation more readable and consistent. 
        
        Adds page to the page stack and stores the page in the pages for history recording.
        """
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])
    
    def selection_wrapper(self, page):
        """ Simple wrapper to make command creation more readable and consistent.
        
        Updates the selection pointer and user choice stack.
        """
        logger.debug(f"selection_wrapper: {page['title']}")

        self.crawl_state['user_choice_stack'].append(page['title'])
        self.pointer['selection'] = page['title']

    # TODO: Fix frayed logic, printing should be separate. use parse_page instead.
    def analyze_page_wrapper(self, page, printing=True, amount=0.1):
        """ Wrapper for analyze_page to make command creation more readable and consistent.
        
        Ensures that all commands that analyze a page have the same behavior.
        
        Args:
            page (dict): The page to analyze.
            printing (bool): Whether to print the results. (interactive mode)
            amount (float): The amount of the page to print.
        """
        # TODO: Named tuple.
        page_tuple = None
        
        try:
            if isinstance(page, Callable):
                logger.debug(f"Unpacked page tuple. {page}")
                page = page()
            elif isinstance(page, tuple) and isinstance(page[1], Callable):
                page = page[1]()
            elif isinstance(page, str):
                page = self.crawler.retrieve(page)
        except Exception as e:
            logger.debug(f"uh? page was {page}", exc_info=e)
                
        if printing or 'stats' not in page:
            page_tuple = analyze_page(page, printing=printing, amount=amount)

            page['stats'] = {}
        
            page['stats']['frequencies'] = page_tuple[3]
            page['stats']['collocations'] = page_tuple[4]

        self.page_wrapper(page)
        self.selection_wrapper(page)

        return page_tuple