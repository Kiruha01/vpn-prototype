import asyncio
import time

from pypacker.layer3.icmp import ICMP, ICMP_ECHO_REPLY
from pypacker.layer3.ip import IP
from pypacker.layer4 import tcp, udp

from pytun import TunTapDevice, IFF_TAP

tun = TunTapDevice(name="test")

tun.addr = "10.10.10.10"
tun.netmask = "255.255.255.0"
tun.mtu = 1500
tun.persist(True)
tun.up()

async def get_async_tun_reader_writer(tun):
    loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader()
    r_protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: r_protocol, tun)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, tun)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer

async def main():
    r, w = await get_async_tun_reader_writer(tun)
    try:
        while True:
            data = await r.read(1500)

            if data[4:5] != b"E":
                continue
            ip = IP(data[4:])
            print(ip)

            new = IP(src_s="10.10.10.45", dst_s="10.10.10.46", p=1) + ICMP(type=ICMP_ECHO_REPLY) +\
                ICMP.Echo(id=123, seq=1, body_bytes=b"foobar")

            w.write(data[:4] + new.bin())
            await w.drain()

    except KeyboardInterrupt:
        pass

    input("Press Enter to exit...")

    tun.down()

    input("Press Enter to exit...")

asyncio.run(main())
