import sys

import pygame

from ball import Ball

# сначала задается константы
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
    clock = pygame.time.Clock() # чтобы контролить фпс

    # создает мячик в центра окна и получает ланные с констант которые были заданы выше
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
            if event.type == pygame.QUIT: # Проверяет события, чтобы закрыть окно через pygame.QUIT. 
                running = False

        pressed = pygame.key.get_pressed() # узнаёт, какие клавиши нажаты сейчас.
        dx = 0
        dy = 0
        # Переменные dx и dy хранят, на сколько сдвинуть мяч по x и y.
        if pressed[pygame.K_UP]:
            dy -= ball.step
        if pressed[pygame.K_DOWN]:
            dy += ball.step
        if pressed[pygame.K_LEFT]:
            dx -= ball.step
        if pressed[pygame.K_RIGHT]:
            dx += ball.step

        if dx != 0 or dy != 0: # Если есть движение, то вызывается метод move объекта ball,
            # который обновляет его позицию на экране, учитывая границы окна (WIDTH и HEIGHT).
            ball.move(dx, dy, WIDTH, HEIGHT)

        screen.fill(BACKGROUND_COLOR) # очищает экран, заполняя его фоновым цветом (BACKGROUND_COLOR).
        ball.draw(screen, pygame) #рисует мячик
        pygame.display.flip() # обновляет экран, отображая все изменения
        clock.tick(FPS) # ограничивает количество кадров в секунду (FPS) до значения, указанного в переменной FPS.

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
