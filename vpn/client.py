import sys

from loguru import logger


import asyncio


class EchoClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, loop):
        self.loop = loop
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        logger.info('Initiated connection')

    def datagram_received(self, data, addr):
        logger.info(f"Received: {data} from {addr}")

    def error_received(self, exc):
        print('Error received:', exc)


loop = asyncio.get_event_loop()
connect = loop.create_datagram_endpoint(
    lambda: EchoClientProtocol(loop),
    remote_addr=('127.0.0.1', 333),
    local_addr=('127.0.0.1', 12345)
)
udp_transport, udp_protocol = loop.run_until_complete(connect)

reader = asyncio.StreamReader()
w_protocol = asyncio.StreamReaderProtocol(reader)
connect = loop.connect_read_pipe(lambda: w_protocol, sys.stdin)
read_transport, read_protocol = loop.run_until_complete(connect)

async def main():
    while True:
        res = await reader.read(255)
        if not res:
            continue

        await loop.sock_sendto(udp_transport, res, ('127.0.0.1', 333))

loop.run_until_complete(main())
loop.run_forever()
udp_transport.close()
loop.close()
