"""Exercise pygame under this repository's real MicroPython interpreter."""

import pygame
from pygame.locals import K_LEFT
from pygame.sprite import Group
from pygame.time import Clock


assert pygame.init() == (2, 0)
screen = pygame.display.set_mode((800, 600))
assert screen.get_size() == (396, 224)
screen.fill("navy")

rect = pygame.Rect(1, 2, 8, 9)
rect.center = (20, 30)
assert rect.center == (20, 30)
assert rect.colliderect((18, 28, 5, 5))

surface = pygame.Surface((8, 8))
surface.fill((255, 0, 0))
surface.set_at((2, 3), (0, 255, 0))
assert surface.get_at((2, 3)).g > 240
pygame.draw.circle(surface, "blue", (4, 4), 2)
pygame.draw.polygon(surface, "white", ((0, 0), (5, 0), (2, 5)))
screen.blit(surface, (10, 10))


class Ball(pygame.sprite.Sprite):
    def __init__(self, x):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((4, 4))
        self.rect = self.image.get_rect(topleft=(x, 0))


left = Ball(0)
right = Ball(2)
balls = Group(left, right)
assert len(balls) == 2
assert len(pygame.sprite.spritecollide(left, balls, False)) == 2
assert K_LEFT == pygame.K_LEFT
assert Clock().tick() >= 0
pygame.display.flip()
pygame.quit()
print("pygame MicroPython smoke: ok")
