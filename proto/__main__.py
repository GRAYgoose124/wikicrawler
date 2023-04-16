from asyncio import Future
from concurrent.futures import ThreadPoolExecutor

import re
import time
import logging

import urllib
from urllib import response
import urllib.request
import urllib.parse

import bs4
from bs4 import BeautifulSoup as bs

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, TextLog, DataTable, Static
from textual.containers import Horizontal, Vertical
from textual.keys import Keys
from textual_autocomplete._autocomplete import InputState, AutoComplete, DropdownItem, Dropdown

from wikicrawler.core.db.cacher import WikiCacher
from wikicrawler.core.utils.config import init_config


class WikiFetcher:
    def __init__(self, parent_logger=None, executor=None) -> None:
        self.logger = parent_logger.getChild(__name__) if parent_logger is not None else logging.getLogger(__name__)
        self._fetches = []
        self._results = []

        self.pool = executor or ThreadPoolExecutor()

        self.config = init_config()
        self.cacher = WikiCacher(self.config, parent_logger=self.logger).start()

        self.__shown_no_token_warning = False

    def limit(self, t=5.0, limit=10):
        """ This is a helper used by fetch to prevent too many requests from happening at once. 

        Checks if the number of fetches in the last t seconds is greater than the limit.
        
        If it is, it will return True, otherwise False.
        """
        # Remove fetches older than t seconds
        for f in self._fetches:
            if f + t < time.perf_counter():
                self._fetches.remove(f)
        
        # Once the number of fetches is greater than the limit, wait t seconds.
        if len(self._fetches) > limit:
            time.sleep(t)
            return True
        else:
            self._fetches.append(time.perf_counter())
            return False
        
    async def fetch(self, url, remote_origin="wikipedia.org") -> bs:
        """
        Fetches a page from the internet.
        
        Args:
            url (str): The url to fetch.

        Returns:
            bs4.BeautifulSoup: The naked page soup.

        Raises:
            urllib.error.HTTPError: If the page is not found or rate limited.
            urllib.error.URLError: If the url is invalid.

        """
        # Throttle requests
        if self.limit():
            return self.queue_request(url)

        parsed_url = urllib.parse.urlparse(url)

        page = None
        if re.search(remote_origin, parsed_url.netloc):
            try:
                req = urllib.request.Request(url)
                try:
                    req.add_header('Authorization', 'Bearer ' + self.config['wiki_api_token'])
                except (ValueError, KeyError, TypeError) as e:
                    if not self.__shown_no_token_warning:
                        self.__shown_no_token_warning = True
                        self.logger.exception("No wiki api token provided. Continuing without one.", exc_info=e)

                response = urllib.request.urlopen(req)
                url = response.geturl()

                page = response.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                self.logger.debug(f"{url} is invalid?", exc_info=e)
            except urllib.error.URLError as e:
                self.logger.debug(f"{url} timed out.", exc_info=e)
    
            if page is not None:
                page_struct = bs(page, 'html.parser')
                page_struct.url = url
                return page_struct

    def queue_request(self, url):
        fut = self.pool.submit(self.fetch, url)
        fut.add_done_callback(self.on_done)
        self.futures.append(fut)
        return fut

    def on_done(self, future):
        r = future.result()

        self.futures.remove(future)

        if r is not None:
            self._results.append(r)
        return r


class AsyncCLI(App):
    CSS_PATH = "app.css"

    def __init__(self, parent_logger=None):
        super().__init__()
        self.logger = parent_logger.getChild(__name__) if parent_logger is not None else logging.getLogger(__name__)
        self.logger.handlers.clear()

        self.executor = ThreadPoolExecutor()
        self.fetcher = WikiFetcher(parent_logger=self.logger, executor=self.executor)

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

        self.input.focus()


    def on_key(self, event):
        if event.key == Keys.Down or event.key == Keys.Tab:
            self.input.focus()
        elif event.key == Keys.Enter:
            self.textlog.write(f"> {self.input.value}")
            fut = self.executor.submit(self.run_cmd, self.input.value)

            self.input.value = ""

    def app_on_done(self, fut):
        results = fut.result()
        self.textlog.write(f"Results: {results}")
        if results is not None:
            self.logger.info(f"{results}")
            # if results is future, get it's results
            if isinstance(results, Future):
                results = results.result()
            if isinstance(results, str):
                [self.textlog.write(line) for line in results.split("\n")]
            elif isinstance(results, list):
                for i, line in enumerate(results):
                    self.textlog.write(f"{i}: {line}")
            elif isinstance(results, dict):
                columns = results.keys()

                for column in columns:
                    if column not in [str(x.label) for x in self.dataview.columns.values()]:
                        self.dataview.add_column(column)


                for column in self.dataview.columns.values():
                    label = str(column.label)

                    if label not in results:
                        results[label] = ""
                
                row = results.values()
                self.dataview.add_row(*row)
             
            else:
                self.textlog.write(results) # TODO: custom page display similar to analyze_page_wrapper/print_results

    def _get_completions(self, input_state: InputState):
        return [DropdownItem("go", "go", "Go to a page")]

    def run_cmd(self, cmd):
        print(f"Running command: {cmd}")

        if any([cmd.startswith(x) for x in ["quit", "exit"]]):
            self.exit()
        
        match cmd.split(" "):
            case ['go', url]:
                self.textlog.write(f"Fetching {url}...")
                fut = self.fetcher.queue_request(url)
                fut.add_done_callback(self.app_on_done)
    

    def exit(self) -> None:
        return super().exit()


if __name__ == "__main__":
    cli = AsyncCLI()
    cli.run()