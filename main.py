import asyncio
from utils import read_txt_async
from loguru import logger
from tasks.zkbridge import start_bridge


async def main():
    wallets: list[str] = await read_txt_async('private_keys.txt')
    logger.info(f'Загружено {len(wallets)} кошельков')

    for wallet in wallets:
        await start_bridge(wallet)


if __name__ == '__main__':
    asyncio.run(main())
