import pygame


pygame.init()
screen = pygame.display.set_mode((396, 224))
clock = pygame.time.Clock()

player = pygame.Rect(182, 100, 32, 24)
running = True

while running:
    for current_event in pygame.event.get():
        if current_event.type == pygame.QUIT:
            running = False

    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_LEFT]:
        player.x -= 3
    if pressed[pygame.K_RIGHT]:
        player.x += 3
    if pressed[pygame.K_UP]:
        player.y -= 3
    if pressed[pygame.K_DOWN]:
        player.y += 3

    player.clamp_ip(screen.get_rect())
    screen.fill((20, 28, 48))
    pygame.draw.rect(screen, (60, 220, 130), player)
    pygame.draw.circle(screen, (255, 210, 60), player.center, 5)
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
