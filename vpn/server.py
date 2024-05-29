import asyncio
import socket

from loguru import logger
from pypacker.layer3.ip import IP
from pytun import TunTapDevice


address_mapping = {}

def init_tun():
    tun = TunTapDevice(name="server")

    tun.addr = "10.10.10.90"
    tun.netmask = "255.255.255.0"
    tun.mtu = 1500
    tun.persist(True)
    tun.up()

    return tun

tun = init_tun()


async def get_async_tun_reader_writer():
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    r_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: r_protocol, tun)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, tun)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer


async def handle_udp_client(server, writer):
    loop = asyncio.get_event_loop()

    while True:
        # Accept new connections
        data, addr = await loop.sock_recvfrom(server, 255)
        logger.debug(f"Process {addr} client")
        if data[4:5] == b"E":
            # if IP protocol
            ip = IP(data[4:])
            print(ip)
            logger.debug(f"Received {ip.higher_layer} from {addr}")

            address_mapping[ip.src] = addr
            logger.debug(f"Saved {ip.src} -> {addr}")

            writer.write(data)
            await writer.drain()
            logger.info(f"Sent {ip.higher_layer.__name__} packet to net")

        # await loop.sock_sendto(server, b"ok\n", addr)


async def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('0.0.0.0', 333))
    server.setblocking(False)

    reader, writer = await get_async_tun_reader_writer()

    loop = asyncio.get_event_loop()

    logger.info(f"Listening on {server.getsockname()}")

    loop.create_task(handle_udp_client(server, writer))

    while True:
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
            if ip.dst in address_mapping:
                logger.info(f"Found {ip.dst} in cache: {address_mapping[ip.dst]}")
                await loop.sock_sendto(server, res, address_mapping[ip.dst])
                logger.info(f"Sent {ip.higher_layer.__name__} packet to client")
            else:
                logger.info(f"Could not find {ip.dst} in cache. Skipping")

asyncio.run(run_server())
