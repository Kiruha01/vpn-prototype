import random
import socket
import sys

from loguru import logger

import asyncio

from pypacker.layer3.ip import IP
from pytun import TunTapDevice

def init_tun(comp_num: int):
    tun = TunTapDevice(name="test" + str(comp_num))

    tun.addr = "10.10.10." + str(comp_num)
    tun.netmask = "255.255.255.0"
    tun.mtu = 1500
    tun.persist(True)
    tun.up()

    logger.info(f"Created tun: {tun.name} on 10.10.10.{comp_num}")

    return tun


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
    logger.info(f"Listening UDP on 0.0.0.0:12346")
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



async def main(server_ip, server_port):
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
        logger.debug(f"Sending ^ to {server_ip}:{server_port}")
        await loop.sock_sendto(client, res, (server_ip, server_port))

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python3 client.py <comp_num> <server address> <server port>")
        exit(1)

    comp_num = int(sys.argv[1])
    server_ip = sys.argv[2]
    server_port = int(sys.argv[3])

    tun = init_tun(comp_num)

    asyncio.run(main(server_ip, server_port))

    tun.down()
