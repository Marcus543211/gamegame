from dataclasses import dataclass
from pygame import Vector2

@dataclass
class RectF:
    bottom_left: Vector2
    size: Vector2

    @property
    def top_right(self):
        return Vector2(self.bottom_left.x + self.width, self.bottom_left.y + self.height)

    @property
    def left(self):
        return self.bottom_left.x
    
    @property
    def right(self):
        return self.top_right.x

    @property
    def bottom(self):
        return self.bottom_left.y

    @property
    def top(self):
        return self.top_right.y

    @property
    def width(self):
        return self.size.x

    @property
    def height(self):
        return self.size.y

    #TODO: Actually make it functional
    def contains(self, other: 'RectF'):
        return True

    def __repr__(self):
        return f"{self.bottom_left}, {self.top_right}"


