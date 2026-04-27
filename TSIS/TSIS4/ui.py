from dataclasses import dataclass

import pygame


PANEL_COLOR = (241, 243, 248)
PANEL_BORDER = (97, 109, 126)
BUTTON_COLOR = (251, 252, 255)
BUTTON_HOVER = (231, 238, 252)
BUTTON_ACTIVE = (175, 206, 255)
BUTTON_TEXT = (28, 32, 39)
TITLE_COLOR = (248, 249, 252)
TEXT_COLOR = (228, 233, 242)


@dataclass
class Button:
    rect: pygame.Rect
    label: str

    def draw(self, screen, font, mouse_pos, active=False):
        hovered = self.rect.collidepoint(mouse_pos)
        fill = BUTTON_ACTIVE if active else BUTTON_HOVER if hovered else BUTTON_COLOR
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, self.rect, 2, border_radius=10)
        label_surface = font.render(self.label, True, BUTTON_TEXT)
        screen.blit(label_surface, label_surface.get_rect(center=self.rect.center))

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


@dataclass
class TextInput:
    rect: pygame.Rect
    text: str = ""
    placeholder: str = ""
    active: bool = True
    max_length: int = 16

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return None

        if event.type != pygame.KEYDOWN or not self.active:
            return None

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
            return "changed"

        if event.key == pygame.K_RETURN:
            return "submit"

        if event.unicode and event.unicode.isprintable() and len(self.text) < self.max_length:
            self.text += event.unicode
            return "changed"

        return None

    def draw(self, screen, font):
        fill = (255, 255, 255) if self.active else (243, 243, 244)
        border = (118, 187, 255) if self.active else PANEL_BORDER
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=10)

        value = self.text if self.text else self.placeholder
        color = (22, 22, 22) if self.text else (120, 120, 120)
        surface = font.render(value, True, color)
        screen.blit(surface, (self.rect.x + 14, self.rect.y + 11))

        if self.active:
            caret_x = self.rect.x + 14 + surface.get_width()
            pygame.draw.line(
                screen,
                (25, 25, 25),
                (caret_x, self.rect.y + 9),
                (caret_x, self.rect.bottom - 9),
                2,
            )


def draw_panel(screen, rect, alpha=214):
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*PANEL_COLOR, alpha), panel.get_rect(), border_radius=18)
    screen.blit(panel, rect.topleft)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=18)


def draw_title(screen, font, text, y):
    surface = font.render(text, True, TITLE_COLOR)
    screen.blit(surface, surface.get_rect(center=(screen.get_width() // 2, y)))


def draw_label(screen, font, text, position, color=TEXT_COLOR):
    surface = font.render(text, True, color)
    screen.blit(surface, position)


def wrap_text(font, text, max_width):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_multiline_label(screen, font, text, position, max_width, color=TEXT_COLOR, line_gap=2):
    x, y = position
    for line in wrap_text(font, text, max_width):
        draw_label(screen, font, line, (x, y), color)
        y += font.get_linesize() + line_gap


def draw_progress_bar(screen, rect, ratio, fill_color, back_color=(55, 62, 76)):
    pygame.draw.rect(screen, back_color, rect, border_radius=8)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=8)
    clamped = max(0.0, min(1.0, ratio))
    inner_width = int((rect.width - 4) * clamped)
    if inner_width > 0:
        fill_rect = pygame.Rect(rect.x + 2, rect.y + 2, inner_width, rect.height - 4)
        pygame.draw.rect(screen, fill_color, fill_rect, border_radius=6)
