import asyncio, socket
from loguru import logger


async def handle_client(server, addr, data):
    loop = asyncio.get_event_loop()
    logger.debug(f"Process {addr} client")
    logger.debug(f"Received {data} from {addr}")

    await loop.sock_sendto(server, b"ok\n", addr)


async def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('0.0.0.0', 333))
    # server.listen(1)
    server.setblocking(False)

    loop = asyncio.get_event_loop()

    logger.info(f"Listening on {server.getsockname()}")

    while True:
        # Accept new connections
        data, addr = await loop.sock_recvfrom(server, 255)
        logger.info(f"Connection from {addr}")
        await loop.create_task(handle_client(server, addr, data))

asyncio.run(run_server())
