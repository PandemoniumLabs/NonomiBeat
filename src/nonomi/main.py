import asyncio
from src.nonomi.core.core import NonomiBeat

async def main():
    app = NonomiBeat()
    await app.main()

if __name__ == "__main__":
    asyncio.run(main())