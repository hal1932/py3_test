# coding: utf-8
from typing import *
import socket
import threading
import struct
import time
import io


class TcpSocket(socket.socket):

    def __init__(self):
        super(TcpSocket, self).__init__(socket.AF_INET, socket.SOCK_STREAM)


class TcpServer(threading.Thread):

    def __init__(self, port):
        # type: (int) -> NoReturn
        self.server = TcpSocket()
        self.server.bind(('localhost', port))
        self.server.listen(1)
        self.timeout = 0.5

    def run(self):
        client = None

        while True:
            if client is None:
                print 'wait for accept'
                client, client_addr = self.server.accept()
                print 'accept: {}'.format(client_addr)

            is_connection_reset = False

            try:
                client.setblocking(False)
                client.sendall(struct.pack('L', 0xDEADBEAF))
            except socket.error as e:
                if e.errno == 10053:
                    print 'send WSAECONNABORTED'
                elif e.errno == 10054:
                    print 'send WSAECONNRESET'
                    is_connection_reset = True
                else:
                    raise e
            finally:
                client.setblocking(True)
                client.settimeout(self.timeout)

            try:
                received_data = client.recv(1024)
                # print 'recv: ' + received_data
            except socket.timeout:
                print 'timeout'
            except socket.error as e:
                if e.errno == 10053:
                    print 'recv WSAECONNABORTED'
                    is_connection_reset = True
                elif e.errno == 10054:
                    print 'recv WSAECONNRESET'
                    is_connection_reset = True
                else:
                    raise e

            data = io.BytesIO()
            data.write(struct.pack('L', 0xBEAF2929))
            data.write(received_data)
            client.sendall(data.getvalue())
            print 'send: {}'.format(received_data)

            if is_connection_reset:
                client = None
                continue

            time.sleep(1)


if __name__ == '__main__':
    server = TcpServer(49152)
    server.run()
