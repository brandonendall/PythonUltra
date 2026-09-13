"""PythonUltra fx-CG50 pygame.image.load() hardware test.

Copy an uncompressed 24-bit BMP named ``sprite.bmp`` beside this script.
Keep calculator-loaded images at or below 56x56 pixels. The display itself is
396x224, but allocating a full-screen RGB565 Surface requires 177408 contiguous
bytes and can exhaust the fx-CG50 MicroPython heap.

Press EXIT to leave the example.
"""

import pygame


pygame.init()
screen = pygame.display.set_mode((396, 224))
sprite = pygame.image.load("sprite.bmp")
rect = sprite.get_rect(center=(198, 112))

running = True
while running:
    for current_event in pygame.event.get():
        if current_event.type == pygame.QUIT:
            running = False
        elif (current_event.type == pygame.KEYDOWN and
              current_event.key == pygame.K_ESCAPE):
            running = False

    screen.fill("black")
    screen.blit(sprite, rect)
    pygame.display.flip()

pygame.quit()
