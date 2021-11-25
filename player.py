import pygame
from pygame import Vector2

from dataclasses import dataclass

@dataclass
class Player:
    acceleration: Vector2 = Vector2(0, 0)
    velocity: Vector2 = Vector2(0, 0)
    position: Vector2 = Vector2(0, 0)
    force: float = 200
    drag: float = 0.004
    #static_drag: float = 0.75

    def __init__(self):
        self.debug = True
        self.font = pygame.font.SysFont('MS UI Gothic', 20)
        self.last_acceleration = Vector2(0, 0)

    def update(self, deltatime):
        self.input()
        self.physics(deltatime)

    @property
    def input_vector(self):
        input = Vector2(0, 0)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: input -= Vector2(0, 1)
        if keys[pygame.K_a]: input -= Vector2(1, 0)
        if keys[pygame.K_s]: input += Vector2(0, 1)
        if keys[pygame.K_d]: input += Vector2(1, 0)
        
        if input.length() != 0:
            return input.normalize()
        else:
            return Vector2(0, 0)

    def input(self):
        self.acceleration += self.input_vector * self.force

    def physics(self, deltatime):
        # Drag
        dragForce = self.velocity.length() ** 2 * self.drag
        if self.velocity.length() != 0:
            self.acceleration -= self.velocity.normalize() * dragForce
        
        # Acceleration, velocity and position
        self.velocity += self.acceleration * deltatime
        self.position += self.velocity * deltatime

        # Reset acceleration
        self.last_acceleration = self.acceleration
        self.acceleration = Vector2(0, 0)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 0, 0), self.position, 50)

        if self.debug:
            screen.blit(self.font.render(f"Position: {self.position}", False, (0, 0, 0)), (0, 0))
            screen.blit(self.font.render(f"Velocity: {self.velocity}", False, (0, 0, 0)), (0, 20))
            screen.blit(self.font.render(f"Acceleration: {self.last_acceleration}", False, (0, 0, 0)), (0, 40))
