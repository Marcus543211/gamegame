from __future__ import annotations

import abc
import logging
import pickle
import socket
import time
from dataclasses import dataclass

import pygame
from pygame import Vector2

from player import Player
from scope import Scope


def get_local_ip():
    return socket.gethostbyname_ex(socket.gethostname())[-1][0]


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


class Server(abc.ABC):
    def __init__(self, address, port=0, sleep=0.01):
        self.sleep = sleep
        self.clients = []

        self._socket = socket.create_server((address, port))
        self._socket.setblocking(False)
        self._socket.listen(1)

        logging.info("Server created on: %s:%s", self.address, self.port)

    @property
    def address(self):
        return self._socket.getsockname()[0]

    @property
    def port(self):
        return self._socket.getsockname()[1]

    def update(self):
        pass

    def handle_connect(self, client, address):
        pass

    def handle_disconnect(self, client, address):
        pass

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
        self.update()

    def _accept_connections(self):
        try:
            connection, address = self._socket.accept()
        except BlockingIOError:
            pass
        else:
            logging.debug("Server accepted client: %s", address)
            self.clients.append((connection, address))
            self.handle_connect(connection, address)

    def _handle_messages(self):
        for connection, address in self.clients:
            try:
                data = connection.recv(4096)
            except BlockingIOError:
                pass
            except ConnectionResetError:
                self._handle_disconnect(connection, address)
            else:
                # Client has disconnected (I think)
                if not data:
                    self._handle_disconnect(connection, address)
                else:
                    logging.debug(
                        "Server received %s from client: %s", data, address)
                    self.handle(connection, address, data)

    def _handle_disconnect(self, connection, address):
        logging.debug("Server lost client: %s", address)
        self.clients.remove((connection, address))
        self.handle_disconnect(connection, address)


class EchoServer(Server):
    def handle(self, _client, _address, data):
        for client, _ in self.clients:
            client.sendall(data)


class GameServer(Server):
    def __init__(self, address, port=0):
        super().__init__(address, port=port)
        self.scope = Scope()
        self.pressed_keys = {}
        self.clock = pygame.time.Clock()

    def update(self):
        deltatime = self.clock.tick() / 1000

        for address, player in self.scope.players.items():
            pressed_keys = self.pressed_keys[address]
            player.update(pressed_keys, deltatime)

            cmd = SetPositionCommand(address, player.position)
            self.send_command(cmd)

    def handle_connect(self, new_client, new_address):
        self.scope.players[new_address] = Player()
        self.pressed_keys[new_address] = set()

        # Add the new player
        cmd = AddPlayerCommand(new_address)
        self.send_command(cmd)

        for client, address in self.clients:
            # Add the old players to the new client
            if address != new_address:
                cmd = AddPlayerCommand(address)
                new_client.sendall(pickle.dumps(cmd))

    def handle_disconnect(self, _client, address):
        del self.scope.players[address]

        cmd = RemovePlayerCommand(address)
        self.send_command(cmd)

    def handle(self, _client, address, data):
        input = pickle.loads(data)

        if isinstance(input, KeyDownInput):
            self.pressed_keys[address].add(input.key)
        elif isinstance(input, KeyUpInput):
            self.pressed_keys[address].discard(input.key)
        else:
            raise Exception(f'Server recived unknown object: {input}')

    def send_command(self, cmd: Command):
        for client, _ in self.clients:
            client.sendall(pickle.dumps(cmd))


class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self, scope: Scope):
        pass


@dataclass
class AddPlayerCommand(Command):
    address: tuple[str, int]

    def execute(self, scope: Scope):
        scope.players[self.address] = Player()


@dataclass
class RemovePlayerCommand(Command):
    address: tuple[str, int]

    def execute(self, scope: Scope):
        del scope.players[self.address]


@dataclass
class SetPositionCommand(Command):
    address: tuple[str, int]
    position: Vector2

    def execute(self, scope: Scope):
        player = scope.players.setdefault(self.address, Player())
        player.position = self.position


class Input:
    pass


@dataclass
class KeyUpInput(Input):
    key: int


@dataclass
class KeyDownInput(Input):
    key: int
