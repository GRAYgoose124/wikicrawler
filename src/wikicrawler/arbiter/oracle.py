import os


class Oracle():
    def __init__(self, root_dir):
        oracle_path = root_dir + "/oracle"

        if not os.path.exists(oracle_path):
            os.makedirs(oracle_path)

        self.oracle_path = oracle_path
        self.brain = None

    def move(self, crawl_state):
        return crawl_state