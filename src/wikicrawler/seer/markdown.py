import os
import json
import logging


logger = logging.getLogger(__name__)


class MarkdownBuilder:
    """ This class provides the ability to compile pages into markdown directories.

    TODO: Mixin as to Seer to expose to seer prompt wrapper.
    """
    def __init__(self, config, cacher=None):
        self.cacher = cacher
        self.root_dir = config['data_root'] + '/markdown'
    
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def build(self, page):
        """ Build a page into markdown.

        This function takes a page and converts it into a markdown directory.
        TODO: Add paragraph links and citation links to markdown.
        """
        page_dir = self.root_dir + '/' + page['title']

        if not os.path.exists(page_dir):
            os.makedirs(page_dir)

        content = ""
        content += f"# {page['title']}\n"

        content += "## Paragraphs\n"
        for paragraph in page['paragraphs']:
            top5 = list(page['stats']['collocations'])[:5]
            if any([" ".join(top) in paragraph for top in top5]):
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

