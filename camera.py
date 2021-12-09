from dataclasses import dataclass

from pygame import Vector2
from pygame import Rect

@dataclass
class Camera:
    position: Vector2 = Vector2(0, 0)
    screen_size: Vector2 = Vector2(1920.0, 1080.0)
    width: float = 10

    @property
    def height(self): 
        return self.width * self.screen_size.y / self.screen_size.x

    @property
    def size(self):
        return Vector2(self.width, self.height)

    @property
    def view_rect(self):
        return Rect(self.position - Vector2(self.width / 2.0, self.height / 2.0), Vector2(self.width / 2.0, self.height / 2.0))
    
    def inside(self, rect: Rect):
        return self.view_rect.contains(rect)

    def pixel_to_world(self, v: Vector2):
        x = v.x / self.screen_size.x * self.width  - self.width / 2  + self.position.x
        y = v.y / self.screen_size.y * self.height - self.height / 2 + self.position.y
        return Vector2(x, y)
        
    def world_to_pixel(self, v: Vector2):
        x = (v.x - self.position.x + self.width / 2)  * self.screen_size.x / self.width
        y = (v.y - self.position.y + self.height / 2) * self.screen_size.y / self.height
        return Vector2(x, y)

    @property
    def pixel_to_world_ratio(self):
        return self.width / self.screen_size.x

    @property
    def world_to_pixel_ratio(self):
        return self.screen_size.x / self.width
    