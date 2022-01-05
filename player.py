from dataclasses import dataclass, field

import pygame
from pygame import Vector2, Rect

from scope import Id


@dataclass
class Player:
    id: Id

    force: Vector2 = field(default_factory = Vector2)
    acceleration: Vector2 = field(default_factory = Vector2)
    velocity: Vector2 = field(default_factory = Vector2)
    position: Vector2 = field(default_factory = Vector2)
    input_force: float = 200
    
    drag: float = 0.08
    radius: float = 0.25
    mass: float = 50

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
        self.force += self.input_vector(keys) * self.input_force

    def physics(self, deltatime):
        # Drag
        drag_force = self.velocity.length() ** 2 * self.drag
        if self.velocity.length() != 0:
            self.acceleration -= self.velocity.normalize() * drag_force

        # Acceleration, velocity and position
        self.acceleration = self.force / self.mass
        self.velocity += self.acceleration * deltatime
        self.position += self.velocity * deltatime

        # Reset acceleration
        self.last_acceleration = Vector2(self.acceleration)
        self.acceleration = Vector2(0, 0)

    def collision(self, others):
        for other in others:
            if self.id > other.id and Vector2.distance_to(self.position, other.position) < self.radius + other.radius:
                m = self.mass
                M = other.mass
                u = self.velocity
                U = other.velocity

                self.velocity =  (2 * M * U - M * u + m * u) / (M + m)
                other.velocity = (M * U - U * m + 2 * m * u) / (M + m)

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
                f"Position: {self.position}", False, (0, 0, 0)), (10, 0))
            scene.screen.blit(self.font.render(
                f"Velocity: {self.velocity}", False, (0, 0, 0)), (10, 20))
            scene.screen.blit(self.font.render(
                f"Acceleration: {self.last_acceleration}", False, (0, 0, 0)), (10, 40))
            scene.screen.blit(self.font.render(
                f"World position: {scene.camera.world_to_pixel(self.position)}", False, (0, 0, 0)), (10, 60))
