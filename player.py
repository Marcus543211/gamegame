from dataclasses import dataclass, field

import pygame
from pygame import Vector2, Rect

import getpass

from id import Id


@dataclass
class Player:
    id: Id
    name: str = getpass.getuser()

    force: Vector2 = field(default_factory = Vector2)
    acceleration: Vector2 = field(default_factory = Vector2)
    velocity: Vector2 = field(default_factory = Vector2)
    position: Vector2 = field(default_factory = Vector2)
    input_force: float = 325
    
    radius: float = 0.5
    mass: float = 50
    drag: float = 4
    brake: float = 25
    incosistent_surface: float = 0.002

    braking: bool = False

    def __post_init__(self):
        self.debug = False
        self.font = pygame.font.SysFont('MS UI Gothic', 20)
        self.last_acceleration = Vector2(0, 0)

    def update(self, pressed_keys, deltatime):
        self.input(pressed_keys)
        self.physics(deltatime)

    def input_vector(self, pressed_keys):
        direction = Vector2(0, 0)
        if pygame.K_w in pressed_keys or pygame.K_UP in pressed_keys:
            direction -= Vector2(0, 1)
        if pygame.K_a in pressed_keys or pygame.K_LEFT in pressed_keys:
            direction -= Vector2(1, 0)
        if pygame.K_s in pressed_keys or pygame.K_DOWN in pressed_keys:
            direction += Vector2(0, 1)
        if pygame.K_d in pressed_keys or pygame.K_RIGHT in pressed_keys:
            direction += Vector2(1, 0)

        if direction.length() != 0:
            return direction.normalize()
        else:
            return Vector2(0, 0)

    def input(self, keys):
        self.force += self.input_vector(keys) * self.input_force
        self.braking = pygame.K_SPACE in keys

    def physics(self, deltatime):
        # Drag
        drag_force = self.velocity.length() ** 2 * self.drag
        if self.velocity.length() != 0:
            self.force -= self.velocity.normalize() * drag_force

        # Brake
        brake_force = self.velocity.length() ** 2 * self.brake
        if self.braking and self.velocity.length() != 0:
            self.force -= self.velocity.normalize() * brake_force

        # Not 'real' physics, but does simulate an inconsistent surface (both on the floor and the ball)
        if self.incosistent_surface > 0:
            if self.velocity.length() > self.incosistent_surface:
                self.velocity -= self.velocity.normalize() * self.incosistent_surface
            else:
                self.velocity -= self.velocity

        # Acceleration, velocity and position
        self.acceleration = self.force / self.mass
        self.velocity += self.acceleration * deltatime
        self.position += self.velocity * deltatime

        # Reset force
        self.force = Vector2(0, 0)

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
        pixelPosition = scene.camera.world_to_pixel(self.position)
        pixelRadius = self.radius * scene.camera.world_to_pixel_ratio

        pygame.draw.circle(scene.screen, (255, 0, 0),
                           pixelPosition,
                           pixelRadius)
        labelPosition = Vector2(pixelPosition.x, pixelPosition.y + pixelRadius * 1.4)
        text = self.font.render(
            self.name,
            True,
            (0, 0, 0)
        )
        text_rect = text.get_rect(center=(labelPosition.x, labelPosition.y))
        scene.screen.blit(text, text_rect)

        if self.debug:
            scene.screen.blit(self.font.render(
                f"Position: {self.position}", False, (0, 0, 0)), (10, 0))
            scene.screen.blit(self.font.render(
                f"Velocity: {self.velocity}", False, (0, 0, 0)), (10, 20))
            scene.screen.blit(self.font.render(
                f"Acceleration: {self.last_acceleration}", False, (0, 0, 0)), (10, 40))
            scene.screen.blit(self.font.render(
                f"World position: {scene.camera.world_to_pixel(self.position)}", False, (0, 0, 0)), (10, 60))
