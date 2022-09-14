from ..seer.markdown import MarkdownBuilder


class Seer(MarkdownBuilder):
    """ Wrapper class for seer commands from the seer module.

    This class is a prompt command wrapper for the seer module, which handles the conversion of
    pages to other formats.
    """
    def __init__(self, prompt, cacher=None):
        super().__init__(prompt.config, cacher=cacher)
        self.prompt = prompt
        self.cacher = cacher

    def handle_build(self):
        self.build(self.prompt.crawl_state['pages'][self.prompt.pointer['selection']])

    def handle_build_hist(self):
        saved_pointer = self.prompt.pointer.copy()

        script = []
        # TODO: generalize "seer build" to use hook and move loop to prompt.iter_hist
        for i in range(len(self.prompt.crawl_state['pages'])):
            script.append(f"st hist {i}")
            script.append("seer build")

        # TODO: standardize run_script
        self.prompt.run_script(script)

        self.prompt.pointer = saved_pointer

    def parse_cmd(self, cmd):
        """
        Handles page conversions.

        This is called by the prompt's parse_cmd function as a sub-parser.


        build [all] - build the current selection (markdown only)

        help - print this help message.
        """
        match cmd:
            case ['build', *hist]:
                if len(hist) >= 1 and hist[0] == 'all':
                    self.handle_build_hist()
                else:
                    self.handle_build()

            case ['help']:
                print(self.parse_cmd.__doc__)
            case _:
                pass
