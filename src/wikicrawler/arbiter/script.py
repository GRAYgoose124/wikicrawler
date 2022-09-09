from functools import partial
import json
import logging
import os
import readline

from io import TextIOWrapper
from collections.abc import Mapping

from .utils.search import print_results, select_result
from ..core.sentiment.paragraph import analyze_page


logger = logging.getLogger(__name__)



# TODO: Metaclass which defines match statement basd on method tree.
class WikiScriptEngine:
    def __init__(self, root_dir, search_precaching=False, cacher=None):
        self.cacher = cacher
        if cacher is not None:
            cacher.register_hook(self.save_state)

        self.search_precaching = search_precaching

        self.root_dir = root_dir 
        self.cli_dir = root_dir + '/data/cli'
        if not os.path.exists(self.cli_dir):
            os.makedirs(self.cli_dir)

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        if os.path.exists(self.cli_dir + '/crawl_state.json'):
            with open(self.cli_dir + '/crawl_state.json', 'r') as f:
                self.crawl_state = json.load(f)
        else:
            self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        
        if os.path.exists(self.cli_dir + '/function_cache.json'):
            with open(self.cli_dir + '/function_cache.json', 'r') as f:
                self.functions = json.load(f)
        else:
            self.functions = {}

        if os.path.exists(self.cli_dir + '/pointer.json'):
            with open(self.cli_dir + '/pointer.json', 'r') as f:
                self.pointer = json.load(f)
        else:
            self.pointer = { 'most_similar_colloc': None, 'selection': None, 'selected_text': None}
    
    # TODO: Use PageCacher to call this.
    def del_state(self):
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_colloc': None, 'selection': None, 'selected_text': None}

        with open(self.cli_dir + '/crawl_state.json', 'w') as f:
            json.dump(self.crawl_state, f)

        with open(self.cli_dir + '/pointer.json', 'w') as f:
            json.dump(self.pointer, f)

    def save_state(self):
        with open(self.cli_dir + '/crawl_state.json', 'w') as f:
            # TODO: make last search just have links in the first place?
            # Removing so partials don't cause a problem. TODO: See above. Need to refactor to remove partials completely.
            if isinstance(self.crawl_state['last_search'][0], tuple):
                self.crawl_state['last_search'] = [e[1].args[0] for e in self.crawl_state['last_search']]
            
            json.dump(self.crawl_state, f)
        
        with open(self.cli_dir + '/function_cache.json', 'w') as f:
            json.dump(self.functions, f)

        with open(self.cli_dir + '/pointer.json', 'w') as f:
            json.dump(self.pointer, f)

    def cmd_func_init(self, name, lines=None):
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
    
    def parse_cmd(self, command):
        raise NotImplementedError("This method must be implemented by a subclass.")

    def loop(self):
        command = ""

        while command != "exit":
            command = input("> ")
            
            self.parse_cmd(command, interactive=True)

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

    # helpers
    def page_wrapper(self, page):
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    # TODO: Fix frayed logic, printing should be separate. use parse_page instead.
    def analyze_page_wrapper(self, page, printing=True):
        page['freq'], page['colloc'] = analyze_page(page, printing=printing)
        return self.page_wrapper(page)
    
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