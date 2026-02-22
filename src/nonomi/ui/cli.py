import asyncio
import readchar

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.nonomi.core.core import NonomiBeat
from src.nonomi.utils.visualizer import Visualizer

class NonomiBeatCLI:
    def __init__(self):
        self.viz = Visualizer()
        self.app = NonomiBeat()
        self.console = Console()
        self.ready_event = asyncio.Event()
        self.stop_viz = asyncio.Event()

    async def start(self, full_screen: bool = False):
        if full_screen:
            self.console.clear()
        self.console.print(Markdown("# NonomiBeat CLI"), style='green')

        ready_event1 = asyncio.Event()
        asyncio.create_task(self.start_backend(ready_event1))

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            progress.add_task("Loading... :3", total=None)
            await ready_event1.wait()

        self.console.print("[green]Ready![/green]")
        self.console.print("[dim]press q to quit[/dim]")

        async def key_listener():
            while True:
                key = await asyncio.to_thread(readchar.readkey)
                if key in ('q', 'Q'):
                    self.stop_viz.set()
                    break

        await asyncio.gather(
            key_listener(),
            self.viz.run_visualizer(self.app.manager.viz_buffer, self.console, self.stop_viz)
        )

    async def start_backend(self, ready_event1: asyncio.Event):
        await self.app.main(ready_event=ready_event1)

    async def stop(self):
        self.console.print("Shutting down... :3", style="green")
        await self.app.stop()