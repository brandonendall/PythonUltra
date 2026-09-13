"""Run in PythonUltra: moving color-key sprites. EXIT quits; F1 toggles key.

Black and magenta sprite backgrounds should disappear with key ON. Movement
should continue across both screen edges without disappearing in mid-screen.
No external BMP is required. This checks the same Surface.blit path as BMPs.
"""
import pygame
import gint
# Import gint before drawing: this port's builtin import hook clears VRAM.
pygame.init()
screen = pygame.display.set_mode((396, 224))
clock = pygame.time.Clock()
black = pygame.Surface((32, 24))
black.fill((0, 0, 0))
pygame.draw.polygon(black, (255, 40, 20), [(0, 11), (29, 1), (24, 11), (29, 22)])
black.set_colorkey((0, 0, 0))
magenta = pygame.Surface((24, 24))
magenta.fill((255, 0, 255))
pygame.draw.circle(magenta, (0, 255, 255), (12, 12), 9)
magenta.set_colorkey((255, 0, 255))
magenta = pygame.transform.flip(magenta, True, False)
enabled = True
x = -32
running = True
try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                enabled = not enabled
                black.set_colorkey((0, 0, 0) if enabled else None)
                magenta.set_colorkey((255, 0, 255) if enabled else None)
        screen.fill((24, 48, 80))
        for gx in range(0, 396, 24):
            pygame.draw.line(screen, (60, 90, 110), (gx, 35), (gx, 223))
        screen.blit(black, (x, 75))
        screen.blit(magenta, (364 - x, 140))
        gint.dtext(3, 3, gint.C_WHITE, 'Color key ' + ('ON' if enabled else 'OFF'))
        gint.dtext(3, 16, gint.C_WHITE, 'F1 toggle   EXIT quit')
        pygame.display.flip()
        x += 3
        if x > 396:
            x = -32
        clock.tick(30)
finally:
    pygame.quit()
