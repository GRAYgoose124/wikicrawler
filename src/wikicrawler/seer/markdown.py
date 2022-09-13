import os
import json
import logging


logger = logging.getLogger(__name__)


class MarkdownBuilder:
    def __init__(self, config, cacher=None):
        self.cacher = cacher
        self.root_dir = config['data_root'] + '/markdown'
    
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def build(self, page):
        page_dir = self.root_dir + '/' + page['title']

        if not os.path.exists(page_dir):
            os.makedirs(page_dir)

        content = ""
        content += f"# {page['title']}\n"

        content += "## Paragraphs\n"
        for paragraph in page['paragraphs']:
            if any([" ".join(top5) in paragraph for top5 in page['stats']['collocations'][:5]]):
                content += paragraph + ' '
        content += '\n'

        content += "## Stats\n"
        for k, v in page['stats'].items():
            content += f"\n### {k}\n"
            for top5 in list(v)[:5]:
                if isinstance(top5, tuple) or isinstance(top5, list):
                    top5 = "_".join(top5)
                content += f"#{top5}\n"

        with open(page_dir + f"/{page['title']}.md", 'w') as f:
            f.write(content)

