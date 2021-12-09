import abc
import atexit
import logging

import pygame
from pygame import Color, Vector2

import network
import ui

from camera import Camera
from scope import Scope

# Pygame skal helst initialiseres så hurtigt så muligt
# Hvis vi begynder at importere klasser, som f.eks. bruger en skrifttype
# som standard parameter, så klager pygame.
pygame.init()

font = pygame.font.SysFont('MS UI Gothic', 24)


class QuitException(Exception):
    pass


# NOTE: "yield from" can be used to give control to another Scene.
# Returning from start returns control to the previous scene
# and QuitException unwinds the entire stack and quits the game.
class Scene(abc.ABC):
    @abc.abstractmethod
    def start(self):
        pass

    def send(self, events):
        if not hasattr(self, '_generator'):
            self._generator = self.start()
            # Make the generator run until the first yield
            self._generator.send(None)

        return self._generator.send(events)

    def __iter__(self):
        return self

    def __next__(self):
        return self.send([])


class MainScene(Scene):
    def __init__(self, screen, client):
        self.screen = screen
        self.camera = Camera()
        self.client = client
        self.clock = pygame.time.Clock()

        self.scope = Scope()

    def start(self):
        while True:
            # Control the framerate
            self.clock.tick(120)

            # Yield control to the main loop and get the events
            events = yield

            # Handle events
            for event in events:
                if event.type == pygame.KEYDOWN:
                    self.client.send(network.KeyDownInput(event.key))
                elif event.type == pygame.KEYUP:
                    self.client.send(network.KeyUpInput(event.key))

            # Ping the server so it doesn't disconnect us
            self.client.send(network.Ping())

            # Receive incoming packets
            while cmd := self.client.recive():
                cmd.execute(self.scope)

            # Draw to the screen
            for player in self.scope.players.values():
                # Draw to the screen
                player.draw(self)


class MainMenuScene(Scene):
    def __init__(self, screen):
        self.screen = screen
        self.should_host = None

        self.server = None
        self.client = None

        atexit.register(self.close)

    def set_should_host(self, should_host):
        self.should_host = should_host

    def start(self):
        # TODO: Make a UI container (flexbox) and UI container scene
        host_button = ui.Button(pos=Vector2(100, 100),
                                child=ui.Text('Host a game', font),
                                callback=lambda: self.set_should_host(True))
        client_button = ui.Button(pos=Vector2(100, 200),
                                  child=ui.Text('Join a game', font),
                                  callback=lambda: self.set_should_host(False))

        while self.should_host is None:
            events = yield
            for event in events:
                host_button.handle(event)
                client_button.handle(event)

            host_button.draw(self.screen)
            client_button.draw(self.screen)

        if self.should_host:
            self.server = network.GameServer('0.0.0.0')
            self.client = network.Client('127.0.0.1', self.server.port)

            host_address = ui.Text(
                f'Connect on address: {network.get_local_ip()}:{self.server.port}',
                font, pos=Vector2(10, 200))

        else:
            self.client = yield from ClientJoinScene(self.screen)

        main_scene = MainScene(self.screen, self.client)

        while True:
            events = yield
            main_scene.send(events)

            if self.server:
                self.server.step()
                host_address.draw(self.screen)

    def close(self):
        # Goodbye networking
        if self.client:
            self.client.close()

        if self.server:
            self.server.close()


class ClientJoinScene(Scene):
    def __init__(self, screen):
        self.screen = screen
        self.address = None

    def set_address(self, address):
        self.address = address

    def start(self):
        msg = 'Please enter the address with port \nto connect to{}: '

        text = ui.Text(msg.format(''), font, pos=Vector2(100, 100))
        entry = ui.Entry(font, Vector2(100, 200), text='127.0.0.1:')
        join = ui.Button(Vector2(100, 300),
                         child=ui.Text('Join', font),
                         callback=lambda: self.set_address(entry.text))

        while True:
            if self.address is not None:
                try:
                    [address, port] = self.address.strip().split(':')
                    return network.Client(address, int(port))
                except (ValueError, OSError):
                    self.address = None
                    text.color = Color('red')
                    text.text = msg.format(' [invalid ip]')

            events = yield

            for event in events:
                text.handle(event)
                entry.handle(event)
                join.handle(event)

            text.draw(self.screen)
            entry.draw(self.screen)
            join.draw(self.screen)


def main():
    # Give me some logging
    logging.basicConfig(level=logging.INFO)

    # Setup pygame
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Ball Bouncing')

    # Create our main scene
    scene = MainMenuScene(screen)

    # Main loop
    while True:
        try:
            events = pygame.event.get()

            if any(event.type == pygame.QUIT for event in events):
                break

            screen.fill(pygame.Color('white'))
            scene.send(events)
            pygame.display.flip()

        except (QuitException, StopIteration):
            break


if __name__ == '__main__':
    main()
