import asyncio
from concurrent.futures import ThreadPoolExecutor

import time

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, TextLog
from textual.keys import Keys

class AsyncCLI(App):
    CSS_PATH = "css/app.css"
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor()
        
        self.textlog = None
        self.input = None

    def compose(self) -> ComposeResult:
        self.textlog = TextLog(classes="box")
        self.input = Input(classes="input")

        yield self.textlog
        yield self.input

    def on_key(self, event):
        if event.key == Keys.Enter:
            self.textlog.write(f"> {self.input.value}")
            self.executor.submit(self.run_cmd, self.input.value)
            self.input.value = ""
        else:
            if event.is_printable:
                self.input.insert_text_at_cursor(event.key)

    async def loop(self):
        with ThreadPoolExecutor() as pool:
            while True:
                try:
                    cmd = input()
                except KeyboardInterrupt:
                    print("Exiting...")
                    break

                if cmd == "exit":
                    break
                
                pool.submit(self.run_cmd, cmd)

    def run_cmd(self, cmd):
        print(f"Running command: {cmd}")

        # Do something with cmd

        time.sleep(1)

        print(f"Command {cmd} finished.")


if __name__ == "__main__":
    cli = AsyncCLI()
    cli.run()