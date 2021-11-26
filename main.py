import abc
import logging

import pygame
from pygame import Vector2, Rect
# Pygame skal helst initialiseres så hurtigt så muligt
# Hvis vi begynder at importere klasser, som f.eks. bruger en skrifttype som standard parameter, så klager pygame
pygame.init()

from player import Player
import network
import ui


class QuitException(Exception):
    pass


# NOTE: "yield from" can be used to give control to another Scene.
# Returning from start returns control to the previous scene
# and QuitException unwinds the entire stack and quits the game.
class Scene(abc.ABC):
    @abc.abstractmethod
    def start(self):
        pass

    def step(self):
        if not hasattr(self, '_generator'):
            self._generator = self.start()

        return self._generator.send(None)

    def __iter__(self):
        return self

    def __next__(self):
        return self.step()


class MainScene(Scene):
    def __init__(self, screen, client):
        self.screen = screen
        self.client = client
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont('MS UI Gothic', 32)
        self.text = ui.Text('Hello\n          world!\n  おはよう', self.font,
                            pos=Vector2(100, 100),
                            size=ui.FixedSize(300, 200))
        self.button = ui.Button(child=ui.Text('Click me', self.font),
                                pos=Vector2(100, 300),
                                callback=lambda: print('Hello from callback!'))
        self.player = Player()

    def start(self):
        while True:
            # Control the framerate
            deltatime = self.clock.tick(120) / 1000

            # Handle events
            for event in pygame.event.get():
                self.button.handle(event)

                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.KEYDOWN:
                    self.client.send(event.key)

            # Receive incoming packets
            while packet := self.client.recive():
                print(packet)

            # Update the player
            self.player.update(deltatime)

            # Draw to the screen
            self.screen.fill(pygame.Color('white'))

            self.player.draw(self.screen)

            self.text.draw(self.screen)
            self.button.draw(self.screen)

            pygame.display.flip()

            # Yield control to the main loop
            yield


def main():
    # Give me some logging
    logging.basicConfig(level=logging.INFO)

    # Set up the networking stuffs
    should_host = input('Host [y/n]? ')

    if 'y' in should_host.lower():
        server = network.EchoServer('0.0.0.0')
        address = ('127.0.0.1', server.port)

        print(f'Connect on address: {network.get_local_ip()}:{server.port}')
    else:
        server = None

        address = input('Please enter the address with port to connect to: ')
        address = tuple(address.strip().split(':'))

    client = network.Client(*address)

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('CrinnedCatters')

    scene = MainScene(screen, client)

    # Main loop
    while True:
        try:
            # Step the scene
            scene.step()
        except (QuitException, StopIteration):
            break
        else:
            # Step the server, if we have one
            if server:
                server.step()

    # Goodbye networking
    client.close()
    if server:
        server.close()


if __name__ == '__main__':
    main()
