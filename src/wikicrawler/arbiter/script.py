import logging
import os
import readline

from io import TextIOWrapper

from .utils.search import print_results, select_result
from ..core.sentiment.paragraph import analyze_page


logger = logging.getLogger(__name__)


# TODO: Metaclass which defines match statement basd on method tree.
class WikiScriptEngine:
    def __init__(self, search_precaching=False):
        self.search_precaching = search_precaching

        self.functions = {}

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_colloc': None, 'selection': None, 'selected_text': None}
        
    def cmd_func_init(self, name):
        function = []
        line = None
        while True:
            line = input("\t")
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
                        self.parse_cmd(command, interactive=False)
            # see if it's just a file object
            elif isinstance(script_or_path, TextIOWrapper):
                for command in script_or_path:
                    self.parse_cmd(command, interactive=False)
            # or try to split the string by \n
            elif '\n' in script_or_path:
                for command in script_or_path.split('\n'):
                    self.parse_cmd(command, interactive=False)
        # otherwise check if it's a list of commands
        elif (isinstance(script_or_path, tuple)
         and len(script_or_path) > 1
         and isinstance(script_or_path[0], str)):
            for command in script_or_path:
                self.parse_cmd(command, interactive=False)
    
    # helpers
    def page_wrapper(self, page):
        self.crawl_state['pages'][page['title']] = page
        self.crawl_state['page_stack'].append(page['title'])

        return page['freq'], page['colloc']

    # TODO: Fixed frayed logic, printing should be separate. use parse_page instead.
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