from collections import deque
from datetime import datetime
from pathlib import Path
import math

import pygame


WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
TOOLBAR_HEIGHT = 150
CANVAS_RECT = pygame.Rect(20, 170, 1060, 570)

BACKGROUND_COLOR = (210, 214, 221)
TOOLBAR_COLOR = (240, 242, 247)
PANEL_BORDER = (140, 148, 160)
CANVAS_COLOR = (255, 255, 255)
TEXT_COLOR = (30, 33, 39)
BUTTON_COLOR = (252, 252, 252)
BUTTON_ACTIVE = (190, 220, 255)
BUTTON_TEXT = (35, 35, 35)

COLORS = {
    "black": (20, 20, 20),
    "red": (220, 50, 47),
    "green": (38, 139, 61),
    "blue": (38, 95, 224),
    "yellow": (235, 179, 48),
    "purple": (135, 78, 196),
}

BRUSH_SIZES = {
    "small": 2,
    "medium": 5,
    "large": 10,
}

TOOL_LABELS = {
    "pencil": "Pencil",
    "line": "Line",
    "eraser": "Eraser",
    "fill": "Fill",
    "text": "Text",
    "rectangle": "Rectangle",
    "circle": "Circle",
    "square": "Square",
    "right_triangle": "Right Tri",
    "equilateral_triangle": "Eq Tri",
    "rhombus": "Rhombus",
}


def get_rect(start, end):
    left = min(start[0], end[0])
    top = min(start[1], end[1])
    width = abs(end[0] - start[0])
    height = abs(end[1] - start[1])
    return pygame.Rect(left, top, width, height)


def get_square_rect(start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    side = min(abs(dx), abs(dy))

    left = start[0] if dx >= 0 else start[0] - side
    top = start[1] if dy >= 0 else start[1] - side
    return pygame.Rect(left, top, side, side)


def get_circle_data(start, end):
    rect = get_rect(start, end)
    center = rect.center
    radius = min(rect.width, rect.height) // 2
    return center, radius


def get_rhombus_points(start, end):
    rect = get_rect(start, end)
    return [
        (rect.centerx, rect.top),
        (rect.right, rect.centery),
        (rect.centerx, rect.bottom),
        (rect.left, rect.centery),
    ]


def get_right_triangle_points(start, end):
    rect = get_rect(start, end)
    return [
        (rect.left, rect.bottom),
        (rect.left, rect.top),
        (rect.right, rect.bottom),
    ]


def get_equilateral_triangle_points(start, end):
    rect = get_rect(start, end)
    side = min(rect.width, int((2 * rect.height) / math.sqrt(3))) if rect.height else 0
    if side <= 0:
        return []

    height = int((math.sqrt(3) / 2) * side)
    top_x = rect.left + rect.width // 2
    top_y = rect.top
    return [
        (top_x, top_y),
        (top_x - side // 2, top_y + height),
        (top_x + side // 2, top_y + height),
    ]


def draw_freehand_segment(surface, color, width, start, end):
    pygame.draw.line(surface, color, start, end, width)
    radius = max(1, width // 2)
    pygame.draw.circle(surface, color, start, radius)
    pygame.draw.circle(surface, color, end, radius)


def draw_shape(surface, tool, color, width, start, end):
    if tool == "line":
        pygame.draw.line(surface, color, start, end, width)
        return

    if tool == "rectangle":
        rect = get_rect(start, end)
        if rect.width > 0 and rect.height > 0:
            pygame.draw.rect(surface, color, rect, width)
        return

    if tool == "circle":
        center, radius = get_circle_data(start, end)
        if radius > 0:
            pygame.draw.circle(surface, color, center, radius, width)
        return

    if tool == "square":
        rect = get_square_rect(start, end)
        if rect.width > 0:
            pygame.draw.rect(surface, color, rect, width)
        return

    if tool == "right_triangle":
        points = get_right_triangle_points(start, end)
        pygame.draw.polygon(surface, color, points, width)
        return

    if tool == "equilateral_triangle":
        points = get_equilateral_triangle_points(start, end)
        if len(points) == 3:
            pygame.draw.polygon(surface, color, points, width)
        return

    if tool == "rhombus":
        points = get_rhombus_points(start, end)
        pygame.draw.polygon(surface, color, points, width)


def flood_fill(surface, start_pos, fill_color):
    x, y = start_pos
    if not (0 <= x < surface.get_width() and 0 <= y < surface.get_height()):
        return 0

    target_color = surface.get_at((x, y))
    replacement = pygame.Color(*fill_color)

    if target_color == replacement:
        return 0

    queue = deque([(x, y)])
    filled = 0

    while queue:
        px, py = queue.pop()
        if not (0 <= px < surface.get_width() and 0 <= py < surface.get_height()):
            continue
        if surface.get_at((px, py)) != target_color:
            continue

        surface.set_at((px, py), replacement)
        filled += 1

        queue.append((px + 1, py))
        queue.append((px - 1, py))
        queue.append((px, py + 1))
        queue.append((px, py - 1))

    return filled


def save_canvas(surface, output_dir):
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = directory / f"paint_{timestamp}.png"
    pygame.image.save(surface, str(filename))
    return filename
