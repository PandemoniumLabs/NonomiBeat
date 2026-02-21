import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from src.nonomi.core.core import NonomiBeat
import readchar

console = Console()
ready_event = asyncio.Event()
app = NonomiBeat()

async def start(full_screen: bool = False):
    if full_screen:
        console.clear()
    console.print(Markdown("# NonomiBeat CLI"), style='green')

    ready_event1 = asyncio.Event()
    asyncio.create_task(start_backend(ready_event1))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
        progress.add_task("Loading... :3", total=None)
        await ready_event1.wait()

    console.print("[green]Ready![/green]")
    console.print("[dim]press q to quit[/dim]")

    while True:
        key = await asyncio.to_thread(readchar.readkey)
        if key in ('q', 'Q'):
            break
    await stop()

async def start_backend(ready_event1: asyncio.Event):
    await app.main(ready_event=ready_event1)

async def stop():
    console.print("Shutting down... :3", style="green")
    await app.stop()