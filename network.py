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


# https://wiki.python.org/moin/UdpCommunication
# https://web.archive.org/web/20180823012240/https://gafferongames.com/categories/game-networking

PROTOCOL_ID = 718420690
PROTOCOL_HEADER = PROTOCOL_ID.to_bytes(4, byteorder='little')

PORT = 39311


class Client:
    def __init__(self, address: str, blocking: bool = False):
        self.host = address

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('127.0.0.1', 0))
        self._socket.setblocking(blocking)

    @property
    def address(self):
        return self._socket.getsockname()[0]

    def recive(self):
        try:
            data, address = self._socket.recvfrom(4096)
        except BlockingIOError:
            return None

        if address[0] == self.host and data.startswith(PROTOCOL_HEADER):
            data = data.removeprefix(PROTOCOL_HEADER)
            return pickle.loads(data)

        return None

    def send(self, obj):
        # I could create a class that buffers the pickler and unpickler with BytesIO
        data = PROTOCOL_HEADER + pickle.dumps(obj)
        self._socket.sendto(data, (self.host, PORT))

    def close(self):
        self._socket.close()


class Server(abc.ABC):
    def __init__(self, address: str, client_timeout: float = 2):
        self.clients = []
        self.timeouts = {}
        self.client_timeout = client_timeout

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((address, PORT))
        self._socket.setblocking(False)

        logging.info("Server created on: %s", self.address)

    @property
    def address(self):
        return self._socket.getsockname()[0]

    def update(self):
        pass

    def handle_connect(self, address: tuple[str, int]):
        pass

    def handle_disconnect(self, address: tuple[str, int]):
        pass

    @abc.abstractmethod
    def handle(self, address: tuple[str, int], data):
        pass

    def close(self):
        logging.info("Server was closed")
        self._socket.close()

    def step(self):
        self._handle_messages()
        self._check_disconnects()
        self.update()

    def sendto(self, address: tuple[str, int], data):
        data = PROTOCOL_HEADER + data
        self._socket.sendto(data, address)

    def _handle_messages(self):
        while True:
            try:
                data, address = self._socket.recvfrom(4096)
            except ConnectionResetError:
                continue
            except BlockingIOError:
                return

            logging.debug("Server received %s from: %s", data, address)

            if data.startswith(PROTOCOL_HEADER):
                data = data.removeprefix(PROTOCOL_HEADER)
                if address in self.clients:
                    self._handle_message(address, data)
                else:
                    self._handle_connect(address, data)

    def _check_disconnects(self):
        timeouts = []

        for address, last_active in self.timeouts.items():
            if time.time() - last_active > self.client_timeout:
                timeouts.append(address)

        for address in timeouts:
            self._handle_disconnect(address)

    def _handle_message(self, address: tuple[str, int], data):
        self.timeouts[address] = time.time()
        self.handle(address, data)

    def _handle_connect(self, address: tuple[str, int], data):
        logging.debug("Server accepted client: %s", address)
        self.clients.append(address)
        self.handle_connect(address)

        self._handle_message(address, data)

    def _handle_disconnect(self, address: tuple[str, int]):
        logging.debug("Server lost client: %s", address)
        self.clients.remove(address)
        del self.timeouts[address]
        self.handle_disconnect(address)


class EchoServer(Server):
    def handle(self, _, data):
        for address in self.clients:
            self.sendto(address, data)


class GameServer(Server):
    def __init__(self, address: str):
        super().__init__(address)

        self.scope = Scope()
        # Pressed keys is a mapping of the players to their set of pressed keys
        self.pressed_keys = {}
        self.clock = pygame.time.Clock()

    def update(self):
        deltatime = self.clock.tick() / 1000

        for address, player in self.scope.players.items():
            # Get the pressed keys of a client and update their player.
            pressed_keys = self.pressed_keys[address]
            player.update(pressed_keys, deltatime)

            # Send a command that sets their new position
            cmd = SetPositionCommand(address, player.position)
            self.send_command(cmd)

    def handle_connect(self, new_address: tuple[str, int]):
        self.scope.players[new_address] = Player()
        self.pressed_keys[new_address] = set()

        # Add the new player to the clients
        cmd = AddPlayerCommand(new_address)
        self.send_command(cmd)

        for address in self.clients:
            # Add the old players to the new client
            if address != new_address:
                cmd = AddPlayerCommand(address)
                self.sendto(address, pickle.dumps(cmd))

    def handle_disconnect(self, address: tuple[str, int]):
        del self.scope.players[address]
        del self.pressed_keys[address]

        cmd = RemovePlayerCommand(address)
        self.send_command(cmd)

    def handle(self, address: tuple[str, int], data):
        input_ = pickle.loads(data)

        if isinstance(input_, KeyDownInput):
            self.pressed_keys[address].add(input_.key)
        elif isinstance(input_, KeyUpInput):
            self.pressed_keys[address].discard(input_.key)
        elif isinstance(input_, Ping):
            pass
        else:
            raise Exception(f'Server recived unknown object: {input_}')

    def send_command(self, cmd: Command):
        for address in self.clients:
            data = pickle.dumps(cmd)
            self.sendto(address, data)


class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self, scope: Scope):
        pass


@dataclass
class AddPlayerCommand(Command):
    address: str

    def execute(self, scope: Scope):
        scope.players[self.address] = Player()


@dataclass
class RemovePlayerCommand(Command):
    address: str

    def execute(self, scope: Scope):
        del scope.players[self.address]


@dataclass
class SetPositionCommand(Command):
    address: str
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


class Ping(Input):
    pass
