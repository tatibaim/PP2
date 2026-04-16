# Этот код определяет класс Ball, который представляет собой шарик, который можно перемещать по экрану.

class Ball:
    def __init__(self, x, y, radius, color, step=20):
        self.x = x 
        self.y = y
        self.radius = radius
        self.color = color
        self.step = step

    def move(self, dx, dy, screen_width, screen_height): 
        new_x = self.x + dx
        new_y = self.y + dy
        
        # тут проверяется, не выходит ли шарик за границы экрана. Если новый x или y находятся
        # в пределах допустимых значений (учитывая радиус шарика), то позиция обновляется. Это
        # гарантирует, что шарик не будет выходить за пределы окна.

        if self.radius <= new_x <= screen_width - self.radius:
            self.x = new_x

        if self.radius <= new_y <= screen_height - self.radius:
            self.y = new_y

    def draw(self, surface, pygame):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
        # просто рисует круг
