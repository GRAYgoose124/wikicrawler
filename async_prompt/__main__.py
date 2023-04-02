import asyncio
from concurrent.futures import ThreadPoolExecutor

import time

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


class AsyncCLI:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    async def run(self):
        session = PromptSession()
        with ThreadPoolExecutor() as pool:
            while True:
                try:
                    with patch_stdout():
                        cmd = await session.prompt_async("> ")
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
    cli.loop.run_until_complete(cli.run())
    cli.loop.close()