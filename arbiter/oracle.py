class Oracle():
    def __init__(self, oracle_path):
        self.oracle_path = oracle_path
        self.brain = None

    def move(self, crawl_state):
        return crawl_state