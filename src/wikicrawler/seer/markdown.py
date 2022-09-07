class MarkdownGrapher:
    def __init__(self, root_dir):
        self.root_dir = root_dir + '/data/markdown'
    

        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)