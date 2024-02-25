import json
from typing import Optional
from aiofiles import open as aio_open
import aiofiles
from pathlib import Path
from typing import List, Union
import asyncio


def read_json(path: str, encoding: Optional[str] = None) -> list | dict:
    return json.load(open(path, encoding=encoding))


async def read_txt_async(filepath: Union[Path, str]) -> List[str]:
    async with aio_open(filepath, "r") as file:
        return [row.strip() async for row in file]
