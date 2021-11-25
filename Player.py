from pygame import Vector2

from dataclasses import dataclass

@dataclass
class Player:
    acceleration: Vector2 = Vector2(0, 0)
    velocity: Vector2 = Vector2(0, 0)
    position: Vector2 = Vector2(0, 0)
    friction: float = 0

    def update(self, deltatime):
        self.velocity += self.acceleration * deltatime
        self.velocity *= 1 - self.friction * deltatime
        self.position += self.velocity * deltatime

    def draw(self, screen):
        pass

