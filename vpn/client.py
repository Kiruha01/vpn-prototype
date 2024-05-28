import socket
import sys

from loguru import logger

import asyncio


async def get_async_stdin_reader():
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    w_protocol = asyncio.StreamReaderProtocol(reader)
    connect = loop.connect_read_pipe(lambda: w_protocol, sys.stdin)
    read_transport, read_protocol = await loop.create_task(connect)
    return reader


def get_udp_transport():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(('0.0.0.0', 12345))
    client.setblocking(False)
    return client


async def handle_server_responses(client):
    loop = asyncio.get_event_loop()
    while True:
        data, addr = await loop.sock_recvfrom(client, 255)
        logger.debug(f"Received {data} from {addr}")


async def main():
    reader = await get_async_stdin_reader()
    client = get_udp_transport()

    loop = asyncio.get_event_loop()

    loop.create_task(handle_server_responses(client))

    while True:
        res = await reader.read(255)
        if not res:
            continue

        await loop.sock_sendto(client, res, ('127.0.0.1', 333))

asyncio.run(main())
