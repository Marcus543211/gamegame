from pygame import *

from dataclasses import dataclass

@dataclass
class Player:
    acceleration: Vector2 = Vector2(0, 0)
    velocity: Vector2 = Vector2(0, 0)
    position: Vector2 = Vector2(0, 0)
    friction: float = 0

    def update(self, deltaTime):
        self.velocity += self.acceleration * deltaTime
        self.velocity *= 1 - self.friction * deltaTime
        self.position += self.velocity * deltaTime

    def draw(self, screen):
        pass

