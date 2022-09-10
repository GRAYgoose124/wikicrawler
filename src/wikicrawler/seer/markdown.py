import os


class MarkdownBuilder:
    def __init__(self, config, cacher=wc):
        self.cacher = cacher
        self.root_dir = config['data_root'] + '/markdown'
    
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def build(self, page):
        pass
