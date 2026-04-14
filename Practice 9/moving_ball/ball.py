"""Ball model for the moving ball pygame exercise."""


class Ball:
    def __init__(self, x, y, radius, color, step=20):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.step = step

    def move(self, dx, dy, screen_width, screen_height):
        """Move the ball only if the new position stays on screen."""
        new_x = self.x + dx
        new_y = self.y + dy

        if self.radius <= new_x <= screen_width - self.radius:
            self.x = new_x

        if self.radius <= new_y <= screen_height - self.radius:
            self.y = new_y

    def draw(self, surface, pygame):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)
