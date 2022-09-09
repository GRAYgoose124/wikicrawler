import logging
import os
import readline

from io import TextIOWrapper


logger = logging.getLogger(__name__)


# TODO: Metaclass which defines match statement basd on method tree.
class WikiScriptEngine:
    def __init__(self):
        self.functions = {}

        # TODO: cache oracle/crawl_states/paths maybe add crawl_state to oracle.
        self.crawl_state = {'user_choice_stack': [], 'page_stack': [], 'pop_stack': [], 'pages': {}, 'last_search': None}
        self.pointer = { 'most_similar_colloc': None, 'selection': None}
        
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