import asyncio
from concurrent.futures import ThreadPoolExecutor

import time
import logging

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, TextLog, DataTable, Static
from textual.containers import Horizontal, Vertical
from textual.keys import Keys
from textual_autocomplete._autocomplete import InputState, AutoComplete, DropdownItem, Dropdown

from .prompt import WikiPrompt
from ..core.crawler import WikiCrawler
from ..core.db.cacher import WikiCacher
from ..core.utils.config import init_config


class AsyncCLI(App):
    CSS_PATH = "utils/app.css"

    def __init__(self, parent_logger=None):
        super().__init__()
        self.logger = parent_logger.getChild(__name__) if parent_logger is not None else logging.getLogger(__name__)

        self.executor = ThreadPoolExecutor()
        
        self.config = init_config()
        self.cacher = WikiCacher(self.config, parent_logger=self.logger).start()
        self.crawler = WikiCrawler(self.config, cacher=self.cacher, parent_logger=self.logger)
        self.prompt = WikiPrompt(self.config, self.crawler, cacher=self.cacher, parent_logger=self.logger)

        self.textlog = None
        self.input = None
        self.autocomplete = None

    def run(self):
        super().run()

        self.input.focus()

    def setup(self):
        self.textlog = TextLog(classes="box", id="textlog")
        self.textlog.can_focus = False
        self.dataview = DataTable(classes="box", id="dataview")
        self.input = Input(id="cmd-input", classes="input")
        self.autocomplete = AutoComplete(self.input, Dropdown(items=self._get_completions, id="input-dropdown"), id="autocomplete-input", classes="input")

    def compose(self) -> ComposeResult:
        self.setup()

        yield Horizontal(
            self.textlog,
            self.dataview,
            classes='column'
        )

        yield self.autocomplete

    def on_key(self, event):
        if not self.autocomplete.has_focus:
            self.input.focus()

        if event.key == Keys.Enter:
            self.textlog.write(f"> {self.input.value}")
            fut = self.executor.submit(self.run_cmd, self.input.value)
            fut.add_done_callback(self.done_callback)

            self.input.value = ""

    def done_callback(self, fut):
        results = fut.result()
        if results is not None:
            self.logger.info(f"{results}")
            if isinstance(results, str):
                [self.textlog.write(line) for line in results.split("\n")]
            elif isinstance(results, list):
                for i, line in enumerate(results):
                    self.textlog.write(f"{i}: {line}")
            elif isinstance(results, dict):
                self.dataview.add_columns(*results.keys())
                self.dataview.add_row(results.values())
            else:
                self.textlog.write(results) # TODO: custom page display similar to analyze_page_wrapper/print_results

    def _get_completions(self, input_state: InputState):
        return [DropdownItem("test", "2", "3")]

    def run_cmd(self, cmd):
        print(f"Running command: {cmd}")

        if cmd == "exit":
            self.exit()

        results = self.prompt.parse_cmd(cmd, interactive=True)
        self.logger.info(f"{results}")
        return results
    

    def exit(self) -> None:
        self.cacher.close()
        return super().exit()


if __name__ == "__main__":
    cli = AsyncCLI()
    cli.run()