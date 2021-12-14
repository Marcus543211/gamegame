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


class UiScene(Scene):
    def __init__(self, screen, widgets: list[ui.Widget]):
        self.screen = screen
        self.widgets = widgets

    def start(self):
        while True:
            events = yield
            for event in events:
                for widget in self.widgets:
                    widget.handle(event)

            for widget in self.widgets:
                widget.draw(self.screen)


class MainScene(Scene):
    def __init__(self, screen, client):
        self.screen = screen
        self.client = client

        self.clock = pygame.time.Clock()
        self.camera = Camera()
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

                # Resize the camera if the window resizes
                elif event.type == pygame.VIDEORESIZE:
                    self.camera.screen_size = Vector2(event.size)

            # Ping the server so it doesn't disconnect us
            self.client.send(network.Ping())

            # Receive incoming packets
            while cmd := self.client.recive():
                cmd.execute(self.scope)

            # Camera follows the player
            #player = self.scope.players.get(self.client.address)
            # if player:
            #    self.camera.position = player.position

            # Draw to the screen
            for player in self.scope.players.values():
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
        host_button = ui.Button(pos=Vector2(100, 100),
                                child=ui.Text('Host a game', font),
                                callback=lambda: self.set_should_host(True))
        client_button = ui.Button(pos=Vector2(100, 200),
                                  child=ui.Text('Join a game', font),
                                  callback=lambda: self.set_should_host(False))

        ui_scene = UiScene(self.screen, [host_button, client_button])

        while self.should_host is None:
            events = yield
            ui_scene.send(events)

        if self.should_host:
            self.server = network.GameServer('0.0.0.0')
            self.client = network.Client('127.0.0.1')

            host_address = ui.Text(
                f'Connect on address: {network.get_local_ip()}',
                font, pos=Vector2(10, self.screen.get_height() - 40))

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
        msg = 'Please enter the address with port to connect to{}: '

        text = ui.Text(msg.format(''), font)
        box = ui.ConstrainedBox(text, ui.Constraints(max_width=400),
                                pos=Vector2(100, 100))
        entry = ui.Entry(font, Vector2(100, 200), text='127.0.0.1:')
        join = ui.Button(Vector2(100, 300),
                         child=ui.Text('Join', font),
                         callback=lambda: self.set_address(entry.text))

        ui_scene = UiScene(self.screen, [box, entry, join])

        while True:
            if self.address is not None:
                try:
                    address = self.address.strip()
                    return network.Client(address)

                except (ValueError, OSError):
                    self.address = None
                    text.color = Color('red')
                    text.text = msg.format(' [invalid ip]')

            events = yield
            ui_scene.send(events)


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
