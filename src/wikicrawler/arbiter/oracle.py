import logging
import os


class Oracle():
    def __init__(self, root_dir, prompt):
        self.prompt = prompt
        oracle_path = root_dir + "/oracle"

        if not os.path.exists(oracle_path):
            os.makedirs(oracle_path)

        self.oracle_path = oracle_path
        self.brain = None

    # TODO: Oracle should compile a summarization of the crawl and user input.
    def parse_cmd(self, command):
        match command:
            case ['div']:
                logging.debug('div proc')