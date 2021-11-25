import abc
import logging
import pickle
import socket
import time


class Server(abc.ABC):
    def __init__(self, address, port=0, sleep=0.01):
        self.sleep = sleep
        self.clients = []

        self._socket = socket.create_server((address, port))
        self._socket.setblocking(False)
        self._socket.listen(1)

        logging.info("Server created on address %s", self.address)

    @property
    def address(self):
        return self._socket.getsockname()

    @abc.abstractmethod
    def handle(self, client, address, data):
        pass

    def serve(self):
        logging.info("Server started serving")

        while True:
            self.step()

            time.sleep(self.sleep)

    def close(self):
        logging.info("Server was closed")
        self._socket.close()

    def step(self):
        self._accept_connections()
        self._handle_messages()

    def _accept_connections(self):
        try:
            connection, address = self._socket.accept()
        except BlockingIOError:
            pass
        else:
            logging.debug("Server accepted client: %s", address)
            self.clients.append((connection, address))

    def _handle_messages(self):
        for connection, address in self.clients:
            try:
                data = connection.recv(4096)
            except BlockingIOError:
                pass
            else:
                # Client has disconnected (I think)
                if not data:
                    logging.debug("Server lost client: %s", address)
                    self.clients.remove((connection, address))
                else:
                    logging.debug(
                        "Server recived %s from client: %s", data, address)
                    self.handle(connection, address, data)


class EchoServer(Server):
    def handle(self, client, address, data):
        for client, _ in self.clients:
            client.sendall(data)


class Client:
    def __init__(self, address, port, blocking=False):
        self.host = (address, port)

        self._socket = socket.create_connection(self.host)
        self._socket.setblocking(blocking)

    def recive(self):
        try:
            data = self._socket.recv(4096)
        except BlockingIOError:
            return None
        else:
            return pickle.loads(data)

    def send(self, obj):
        # I could create a class that buffers the pickler and unpickler with BytesIO
        data = pickle.dumps(obj)
        self._socket.sendall(data)

    def close(self):
        self._socket.close()
