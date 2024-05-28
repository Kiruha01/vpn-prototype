import asyncio, socket
import time

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

        loop.create_task(loop.sock_sendto(self.transport, b"ok\n", addr))
        logger.info(f"Send ok to {addr}")
        time.sleep(4)

        loop.create_task(loop.sock_sendto(self.transport, b"ok 2\n", addr))
        logger.info(f"Send ok 2 to {addr}")


    def error_received(self, exc):
        print('Error received:', exc)

loop = asyncio.get_event_loop()
connect = loop.create_datagram_endpoint(
    lambda: EchoClientProtocol(loop),
    local_addr=('127.0.0.1', 333))
transport, protocol = loop.run_until_complete(connect)
loop.run_forever()
transport.close()
loop.close()

#
# async def handle_client(server, addr, data):
#     loop = asyncio.get_event_loop()
#     logger.debug(f"Process {addr} client")
#     logger.debug(f"Received {data} from {addr}")
#
#     await loop.sock_sendto(server, b"ok\n", addr)
#
#     logger.debug(f"Send ok to {addr}")
#
#
# async def run_server():
#     server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server.bind(('10.10.10.1', 333))
#     # server.listen(1)
#     server.setblocking(False)
#
#     loop = asyncio.get_event_loop()
#
#     logger.info(f"Listening on {server.getsockname()}")
#
#     while True:
#         # Accept new connections
#         data, addr = await loop.sock_recvfrom(server, 255)
#         logger.info(f"Connection from {addr}")
#         await loop.create_task(handle_client(server, addr, data))
#
# asyncio.run(run_server())
