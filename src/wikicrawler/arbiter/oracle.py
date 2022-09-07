import os


class Oracle():
    def __init__(self, root_dir, prompt):
        self.prompt = prompt
        oracle_path = root_dir + "/oracle"

        if not os.path.exists(oracle_path):
            os.makedirs(oracle_path)

        self.oracle_path = oracle_path
        self.brain = None

    def move(self, jump_phrase):
        self.prompt.parse_cmd(f'st sim_colloc 0 {jump_phrase}')
        self.prompt.parse_cmd(f"s {self.prompt.pointer['most_similar_colloc']}")
        self.prompt.parse_cmd(f'st sel 0')
        # self.prompt.crawl_state