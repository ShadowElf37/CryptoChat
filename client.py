from threading import Thread
from queue import Queue
import socket


class Client:
    def __init__(self):
        self.conn = BaseClient('73.166.38.74', 37378)
        self.table: {str: str} = {}

    def _update_table(self, msg: bytes):
        split = -1
        for i, charcode in enumerate(msg):
            if charcode == ord('\n'):
                split = i
                break
        if split == -1:
            return


    def _send_to(self, name, message: bytes):
        dst = self.table.get(name)
        if dst is None:
            return
        self.conn.write(dst+b'\n'+message)

class BaseClient:
    NOQUEUE = object()  # return this from read_cb to avoid queuing received messages (i.e. we handled it somewhere else)

    def __init__(self, ip, port, read_cb=lambda byt: None):
        self.client_addr = ip, port
        self.socket = socket.socket()
        self.socket.connect(self.client_addr)

        self.is_open = False
        self.reader_thread = Thread(target=self._read_all, daemon=True)
        self.writer_thread = Thread(target=self._write_all, daemon=True)
        self._messages = Queue()
        self._write_queue = Queue()

        self.read_cb = read_cb

    def __iter__(self):
        while not self._messages.empty():
            yield self._messages.get()

    def write(self, msg: bytes):
        self._write_queue.put(msg)

    def read(self):
        """Gets a message, or nothing"""
        if self._messages.empty():
            return
        return self._messages.get()

    def wait_read(self):
        """Waits for a message before returning"""
        return self._messages.get()

    def close(self):
        self.is_open = False
        self.socket.close()

    def open(self):
        self.is_open = True
        self.reader_thread.start()
        self.writer_thread.start()

    def _read_all(self):
        try:
            while self.is_open:
                m = self.socket.recv(1024)
                if self.read_cb(m) is not self.NOQUEUE:
                    self._messages.put(m)
        except ConnectionError:
            self.is_open = False
            print('Connection broke (read thread).')

    def _write_all(self):
        try:
            while self.is_open:
                self.socket.send(self._write_queue.get())
        except ConnectionError:
            self.is_open = False
            print('Connection broke (write thread).')