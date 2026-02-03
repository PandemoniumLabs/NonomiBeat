from src.nonomi.core.core import NonomiBeat
import asyncio

async def main():
    app = NonomiBeat(patch_path="src/nonomi/patches/main.pd")
    try:
        await app.start()

    except asyncio.CancelledError:
        pass

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt or asyncio.CancelledError:
        print("Exiting…")
