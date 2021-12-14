from dataclasses import dataclass, field

import pygame
from pygame import Rect, Vector2


def get_screen_size() -> Vector2:
    return Vector2(pygame.display.get_surface().get_size())


@dataclass
class Camera:
    position: Vector2 = field(default_factory=Vector2)
    screen_size: Vector2 = field(default_factory=get_screen_size)
    width: float = 10

    @property
    def height(self):
        return self.width * self.screen_size.y / self.screen_size.x

    @property
    def size(self):
        return Vector2(self.width, self.height)

    @property
    def view_rect(self):
        return Rect(self.position - self.size / 2, self.size / 2)

    def inside(self, rect: Rect):
        return self.view_rect.contains(rect)

    def pixel_to_world(self, pos: Vector2):
        x = pos.x / self.screen_size.x * self.width - self.width / 2 + self.position.x
        y = pos.y / self.screen_size.y * self.height - self.height / 2 + self.position.y
        return Vector2(x, y)

    def world_to_pixel(self, pos: Vector2):
        return (pos - self.position + self.size / 2) * self.world_to_pixel_ratio

    @property
    def pixel_to_world_ratio(self):
        return self.width / self.screen_size.x

    @property
    def world_to_pixel_ratio(self):
        return self.screen_size.x / self.width
