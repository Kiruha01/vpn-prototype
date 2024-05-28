import random
import socket
import sys

from loguru import logger

import asyncio

from pypacker.layer3.ip import IP
from pytun import TunTapDevice

def init_tun():
    rnd = random.randint(0, 100)
    tun = TunTapDevice(name="test" + str(rnd))

    tun.addr = "10.10.10." + str(rnd)
    tun.netmask = "255.255.255.0"
    tun.mtu = 1500
    tun.persist(False)
    tun.up()

    print("Random:", rnd)

    return tun

tun = init_tun()

async def get_async_stdin_reader():
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    w_protocol = asyncio.StreamReaderProtocol(reader)
    connect = loop.connect_read_pipe(lambda: w_protocol, sys.stdin)
    read_transport, read_protocol = await loop.create_task(connect)
    return reader


async def get_async_tun_reader_writer():
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    r_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: r_protocol, tun)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, tun)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer


def get_udp_transport():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(('0.0.0.0', 12346))
    client.setblocking(False)
    return client


async def handle_server_responses(client, tun_wirter):
    loop = asyncio.get_event_loop()
    while True:
        data, addr = await loop.sock_recvfrom(client, 1500)
        logger.debug(f"Received from {addr}")
        if data[4:5] == b"E":
            # if IP protocol
            ip = IP(data[4:])
            print(ip)

            tun_wirter.write(data)
            await tun_wirter.drain()
            logger.debug("Recieved and sent to tun")
            continue

        logger.debug(f"Not IP: {data}")
        # if not IP protocol
        # tun_wirter.write(data)
        # await tun_wirter.drain()
        # logger.debug("Recieved and sent to tun 2")



async def main():
    reader, writer = await get_async_tun_reader_writer()
    client = get_udp_transport()

    loop = asyncio.get_event_loop()

    loop.create_task(handle_server_responses(client, writer))

    while True:
        res = await reader.read(1500)
        if not res:
            continue

        if res[4:5] != b"E":
            logger.debug("Not IP")
            # if not IP protocol
            continue
        ip = IP(res[4:])
        print(ip)
        logger.debug(f"Sending ^ to 127.0.0.1:333")
        await loop.sock_sendto(client, res, ('127.0.0.1', 333))

asyncio.run(main())

tun.down()
