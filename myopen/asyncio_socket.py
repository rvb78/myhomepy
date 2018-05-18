# -*- coding: utf-8 -*-

import asyncio
import asyncio.events as events
import socket
from asyncio.streams import (_DEFAULT_LIMIT, StreamReader,
                             StreamReaderProtocol, StreamWriter)

from core.logger import *


class AsyncIOSock(object):
    def __init__(self, host, port, loop=None, log=None):
        self.host = host
        self.port = port
        self.loop = loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()
        self.log = log
        self.connected = False
        self.sock = None

    async def _sock_connect(self, sock):
        # catch socket.gaierror
        while not self.connected:
            try:
                self.log('attempt socket connection')
                sock.connect((self.host, self.port))
            except (socket.gaierror, socket.timeout) as e:
                self.log('unable to connect to %s:%d' % (self.host, self.port))
                self.log('wait 10s')
                await asyncio.sleep(10)
                continue
            self.connected = True

    async def _gen_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
        sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 2)
        sock.settimeout(1)
        await self._sock_connect(sock)
        sock.setblocking(0)
        return sock

    def stop(self):
        if self.sock is not None:
            self.log('socket shutdown', LOG_INFO)
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.log('socket close', LOG_INFO)
            self.sock.close()

    async def readuntil(self, sep=b'##'):
        pos = 0
        done = False
        pkt = b''
        while not done:
            sep_at_pos = bytes(sep[pos:pos+1])
            try:
                b = await self.loop.sock_recv(self.sock, 1)
            except TimeoutError:
                self.connected = False
                raise ConnectionAbortedError
            if b == sep_at_pos:
                pos += 1
                if pos >= len(sep):
                    done = True
            else:
                pos = 0
            pkt += b
        return pkt

    async def write(self, pkt):
        await self.loop.sock_sendall(self.sock, pkt)

    async def connect(self):
        self.sock = await self._gen_sock()

    async def get_packet(self):
        msg = await self.readuntil()
        msg = msg.decode(encoding='ascii')
        self.log('<= %s' % (msg))
        return msg

    async def send_packet(self, msg):
        self.log('=> %s' % (msg))
        msg = msg.encode(encoding='ascii')
        await self.write(msg)
