import pygame
from pygame import Vector2, Rect

from dataclasses import dataclass, field


@dataclass
class Player:
    acceleration: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    position: Vector2 = field(default_factory=Vector2)
    force: float = 3
    drag: float = 0.006
    radius: float = 0.25
    #static_drag: float = 0.75

    def __post_init__(self):
        self.debug = True
        self.font = pygame.font.SysFont('MS UI Gothic', 20)
        self.last_acceleration = Vector2(0, 0)

    def update(self, pressed_keys, deltatime):
        self.input(pressed_keys)
        self.physics(deltatime)

    def input_vector(self, pressed_keys):
        direction = Vector2(0, 0)
        if pygame.K_w in pressed_keys:
            direction -= Vector2(0, 1)
        if pygame.K_a in pressed_keys:
            direction -= Vector2(1, 0)
        if pygame.K_s in pressed_keys:
            direction += Vector2(0, 1)
        if pygame.K_d in pressed_keys:
            direction += Vector2(1, 0)

        if direction.length() != 0:
            return direction.normalize()
        else:
            return Vector2(0, 0)

    def input(self, keys):
        self.acceleration += self.input_vector(keys) * self.force

    def physics(self, deltatime):
        # Drag
        drag_force = self.velocity.length() ** 2 * self.drag
        if self.velocity.length() != 0:
            self.acceleration -= self.velocity.normalize() * drag_force

        # Acceleration, velocity and position
        self.velocity += self.acceleration * deltatime
        self.position += self.velocity * deltatime

        # Reset acceleration
        self.last_acceleration = self.acceleration
        self.acceleration = Vector2(0, 0)

    @property
    def bounding_box(self):
        bottom_left = self.position - Vector2(self.radius)
        return Rect(bottom_left, Vector2(2 * self.radius))

    def draw(self, scene):
        pygame.draw.circle(scene.screen, (255, 0, 0),
                           scene.camera.world_to_pixel(self.position),
                           self.radius * scene.camera.world_to_pixel_ratio)

        if self.debug:
            scene.screen.blit(self.font.render(
                f"Position: {self.position}", False, (0, 0, 0)), (0, 0))
            scene.screen.blit(self.font.render(
                f"Velocity: {self.velocity}", False, (0, 0, 0)), (0, 20))
            scene.screen.blit(self.font.render(
                f"Acceleration: {self.last_acceleration}", False, (0, 0, 0)), (0, 40))
            scene.screen.blit(self.font.render(
                f"World position: {scene.camera.world_to_pixel(self.position)}", False, (0, 0, 0)), (0, 60))
