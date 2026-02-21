import asyncio
from src.nonomi.ui.cli import start
import argparse

parser = argparse.ArgumentParser(
    prog='NonomiBeat',
    description='An adaptive LoFi generator'
)
parser.add_argument(
    "--mode", choices=["cli", "tui"], default="cli",
    help="Choose the interface mode (default: cli)"
)
parser.add_argument(
    "--fs", action='store_true',
    help="Clear terminal and run in 'full-screen' mode for CLI"
)
args = parser.parse_args()

async def main():
    if args.mode == "cli":
        await start(True if args.fs else False)

    elif args.mode == "tui":
        print("TUI mode is not implemented yet. Please use CLI mode.")

if __name__ == "__main__":
    asyncio.run(main())