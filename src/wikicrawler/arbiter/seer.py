from ..seer.markdown import MarkdownBuilder


class Seer(MarkdownBuilder):
    def __init__(self, prompt, cacher=None):
        super().__init__(prompt.config, cacher=cacher)
        self.prompt = prompt
        self.cacher = cacher

    def parse_cmd(self, cmd):
        """
        Handles page conversions.

        build - build the current selection (markdown only)

        help - print this help message.
        """
        match cmd:
            case ['build']:
                self.build(self.prompt.crawl_state['pages'][self.prompt.pointer['selection']])
            case ['help']:
                print(self.parse_cmd.__doc__)
            case _:
                pass
