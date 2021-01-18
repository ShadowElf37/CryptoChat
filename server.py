import socket
from threading import Thread
from queue import Queue

s = socket.socket()
s.bind(('0.0.0.0', 37378))
s.listen(0)

clients: {tuple: socket.socket} = {}
messages = Queue()

def accept_clients():
    while True:
        c, a = s.accept()
        clients[a] = c
        Thread(target=read_into, daemon=True, args=(c, a, messages)).start()

def read_into(conn, addr, queue):
    try:
        while True:
            queue.put(conn.recv(8192))
    except ConnectionError:
        del clients[addr]

Thread(target=accept_clients, daemon=True).start()
while True:
    m = messages.get()
    split = -1
    for i, charcode in enumerate(m):
        if charcode == ord('\n'):
            split = i
            break

    if split == -1:
        continue

    ip, port = m[:split].decode().split(':')  # host:port
    port = int(port)

    if (ip, port) in clients:
        clients[(ip, port)].send(m)