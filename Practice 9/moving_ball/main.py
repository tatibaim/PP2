import sys

import pygame

from ball import Ball


WIDTH, HEIGHT = 600, 400
BACKGROUND_COLOR = (255, 255, 255)
FPS = 60
BALL_SPEED = 4
BALL_RADIUS = 25
BALL_COLOR = (255, 0, 0)


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Moving Ball Game")
    clock = pygame.time.Clock()

    ball = Ball(
        x=WIDTH // 2,
        y=HEIGHT // 2,
        radius=BALL_RADIUS,
        color=BALL_COLOR,
        step=BALL_SPEED,
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pressed = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if pressed[pygame.K_UP]:
            dy -= ball.step
        if pressed[pygame.K_DOWN]:
            dy += ball.step
        if pressed[pygame.K_LEFT]:
            dx -= ball.step
        if pressed[pygame.K_RIGHT]:
            dx += ball.step

        if dx != 0 or dy != 0:
            ball.move(dx, dy, WIDTH, HEIGHT)

        screen.fill(BACKGROUND_COLOR)
        ball.draw(screen, pygame)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
