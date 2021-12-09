from dataclasses import dataclass, field

from pygame import Vector2
from pygame import Rect


@dataclass
class Camera:
    position: Vector2 = field(default_factory=Vector2)
    screen_size: Vector2 = field(default_factory=lambda: Vector2(800, 600))
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

    def pixel_to_world(self, v: Vector2):
        x = v.x / self.screen_size.x * self.width - self.width / 2 + self.position.x
        y = v.y / self.screen_size.y * self.height - self.height / 2 + self.position.y
        return Vector2(x, y)

    def world_to_pixel(self, v: Vector2):
        return (v - self.position + self.size / 2) * self.world_to_pixel_ratio

    @property
    def pixel_to_world_ratio(self):
        return self.width / self.screen_size.x

    @property
    def world_to_pixel_ratio(self):
        return self.screen_size.x / self.width
