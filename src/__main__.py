from .nonomi.core.core import NonomiBeat
import asyncio

async def main():
    try:
        app = NonomiBeat(patch_path="src/nonomi/patches/main.pd")
        await app.start()

    except KeyboardInterrupt:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())