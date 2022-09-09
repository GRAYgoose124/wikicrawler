import logging
import os


logger = logging.getLogger(__name__)


class Oracle():
    def __init__(self, prompt):
        self.prompt = prompt

        oracle_path = prompt.root_dir + "/data/oracle"
        self.oracle_path = oracle_path

        if not os.path.exists(oracle_path):
            os.makedirs(oracle_path)

        self.brain = None

    def handle_freq_move(self, jump_phrase):
        pass

    # TODO: refactor into file.
    def handle_colloc_move(self, jump_phrase):
        self.prompt.run_script(f"st colloc {jump_phrase}",
                        f"s most_similar_colloc",
                        "st found 0")

    # TODO: Oracle should compile a summarization of the crawl and user input.
    def parse_cmd(self, command):
        """
        Parse the command and return the function and arguments.

        div - divine traversal state

        cmov <phrase> - move to first page matched by phrase==collocations of current page.
        fmov <phrase> - move to first page matched by phrase==frequency of current page.

        help - show help
        """
        match command:
            case ['div']:
                logger.debug('div proc')

            case ['cmov', *jump_phrase]:
                self.handle_colloc_move(" ".join(jump_phrase))

            case ['fmov', *jump_phrase]:
                self.handle_freq_move(" ".join(jump_phrase))

            case ['help']:
                print(self.parse_cmd.__doc__)
