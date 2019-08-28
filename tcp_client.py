# coding: utf-8
from typing import *
import socket
import struct
import time


class TcpClient(object):

    def __init__(self):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        # type: (str, int) -> NoReturn
        self.__sock.connect((host, port))

    def send(self, data):
        # type: (bytes) -> NoReturn
        self.__sock.sendall(data)

    def recv(self, count):
        # type: (int) -> bytes
        return self.__sock.recv(count)


if __name__ == '__main__':
    client = TcpClient()
    client.connect('localhost', 49152)

    i = 0

    while True:
        data = client.recv(1024)
        print '-----'
        print 'recv size: {}'.format(len(data))

        offset = 0
        while offset < len(data):
            code = struct.unpack_from('L', data, offset)[0]
            offset += 4
            if code == 0xDEADBEAF:
                print 'ping'
            elif code == 0xBEAF2929:
                print data[offset]
                offset += 1
            else:
                print '??? {}: {}'.format(code, data)
        print '-----'

        if i < 10:
            client.send(str(i))

        time.sleep(2)
        i += 1
