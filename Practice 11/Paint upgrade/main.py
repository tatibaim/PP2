import math
import pygame

# NEW: upgraded paint with extra shapes and live shape preview
def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 560))
    clock = pygame.time.Clock()
    
    radius = 15
    color_mode = 'blue'
    tool = 'brush'
    drawings = []
    current_stroke = None
    shape_start = None
    # NEW: stores current mouse position for live preview while dragging shapes
    current_mouse_pos = None
    drawing = False
    
    while True:
        
        pressed = pygame.key.get_pressed()
        
        alt_held = pressed[pygame.K_LALT] or pressed[pygame.K_RALT]
        ctrl_held = pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]
        
        for event in pygame.event.get():
            
            # determin if X was clicked, or Ctrl+W or Alt+F4 was used
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w and ctrl_held:
                    return
                if event.key == pygame.K_F4 and alt_held:
                    return
                if event.key == pygame.K_ESCAPE:
                    return
             
                # determine if a letter key was pressed
                if event.key == pygame.K_r:
                    color_mode = 'red'
                elif event.key == pygame.K_g:
                    color_mode = 'green'
                elif event.key == pygame.K_b:
                    color_mode = 'blue'
                elif event.key == pygame.K_p:
                    tool = 'brush'
                elif event.key == pygame.K_e:
                    tool = 'eraser'
                elif event.key == pygame.K_o:
                    tool = 'circle'
                elif event.key == pygame.K_t:
                    tool = 'rectangle'
                # NEW: extra shape hotkeys
                elif event.key == pygame.K_s:
                    tool = 'square'
                elif event.key == pygame.K_d:
                    tool = 'diamond'
                elif event.key == pygame.K_y:
                    tool = 'right_triangle'
                elif event.key == pygame.K_u:
                    tool = 'equilateral_triangle'
                elif event.key == pygame.K_c:
                    drawings.clear()
             
                if event.key == pygame.K_UP:
                    radius = min(200, radius + 1)
                elif event.key == pygame.K_DOWN:
                    radius = max(1, radius - 1)

             
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    current_mouse_pos = event.pos
                    if tool == 'brush' or tool == 'eraser':
                        current_stroke = {
                            "type": "stroke",
                            "mode": color_mode if tool == 'brush' else 'eraser',
                            "radius": radius,
                            "points": [event.pos]
                        }
                        drawings.append(current_stroke)
                    else:
                        shape_start = event.pos
                    drawing = True

            if event.type == pygame.MOUSEMOTION and drawing:
                current_mouse_pos = event.pos
                if current_stroke is not None:
                    current_stroke["points"].append(event.pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if drawing and shape_start is not None:
                        drawings.append({
                            "type": tool,
                            "mode": color_mode,
                            "width": max(1, radius // 4),
                            "start": shape_start,
                            "end": event.pos
                        })
                    drawing = False
                    current_stroke = None
                    shape_start = None
                    current_mouse_pos = None
                   
                   
        screen.fill((0, 0, 0))
        
        for drawing_item in drawings:
            if drawing_item["type"] == "stroke":
                draw_stroke(screen, drawing_item)
            else:
                draw_shape(screen, drawing_item)

        # NEW: preview shape before mouse button is released
        if drawing and shape_start is not None and current_mouse_pos is not None:
            draw_shape(screen, {
                "type": tool,
                "mode": color_mode,
                "width": max(1, radius // 4),
                "start": shape_start,
                "end": current_mouse_pos
            })

        draw_ui(screen, tool, color_mode, radius)
        
        pygame.display.flip()
        
        clock.tick(60)

def get_base_color(color_mode):
    if color_mode == 'blue':
        return (0, 0, 255)
    elif color_mode == 'red':
        return (255, 0, 0)
    elif color_mode == 'green':
        return (0, 255, 0)
    elif color_mode == 'eraser':
        return (0, 0, 0)

    return (255, 255, 255)

def get_color(index, color_mode):
    if color_mode == 'eraser':
        return get_base_color(color_mode)

    c1 = max(0, min(255, 2 * index - 256))
    c2 = max(0, min(255, 2 * index))
    
    if color_mode == 'blue':
        return (c1, c1, c2)
    elif color_mode == 'red':
        return (c2, c1, c1)
    elif color_mode == 'green':
        return (c1, c2, c1)

    return (255, 255, 255)

def draw_stroke(screen, stroke):
    points = stroke["points"]
    stroke_mode = stroke["mode"]
    stroke_radius = stroke["radius"]

    if len(points) == 1:
        pygame.draw.circle(
            screen,
            get_color(0, stroke_mode),
            points[0],
            stroke_radius
        )
        return

    i = 0
    while i < len(points) - 1:
        drawLineBetween(
            screen,
            i,
            points[i],
            points[i + 1],
            stroke_radius,
            stroke_mode
        )
        i += 1

def get_rect(start, end):
    left = min(start[0], end[0])
    top = min(start[1], end[1])
    width = abs(start[0] - end[0])
    height = abs(start[1] - end[1])
    return pygame.Rect(left, top, width, height)

# NEW: helper for perfect square
def get_square_rect(start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    side = min(abs(dx), abs(dy))

    left = start[0] if dx >= 0 else start[0] - side
    top = start[1] if dy >= 0 else start[1] - side
    return pygame.Rect(left, top, side, side)

# NEW: helper for diamond points
def get_diamond_points(start, end):
    rect = get_rect(start, end)
    center_x = rect.left + rect.width // 2
    center_y = rect.top + rect.height // 2
    return [
        (center_x, rect.top),
        (rect.right, center_y),
        (center_x, rect.bottom),
        (rect.left, center_y),
    ]

# NEW: helper for right triangle points
def get_right_triangle_points(start, end):
    rect = get_rect(start, end)
    return [
        (rect.left, rect.top),
        (rect.left, rect.bottom),
        (rect.right, rect.bottom),
    ]

# NEW: helper for equilateral triangle points
def get_equilateral_triangle_points(start, end):
    rect = get_rect(start, end)
    side = min(rect.width, int((2 * rect.height) / math.sqrt(3)))

    if side <= 0:
        return []

    height = int((math.sqrt(3) / 2) * side)
    center_x = rect.left + rect.width // 2
    top = rect.top

    return [
        (center_x, top),
        (center_x - side // 2, top + height),
        (center_x + side // 2, top + height),
    ]

def draw_shape(screen, shape):
    color = get_base_color(shape["mode"])
    width = shape["width"]
    start = shape["start"]
    end = shape["end"]

    if shape["type"] == "rectangle":
        rect = get_rect(start, end)
        pygame.draw.rect(screen, color, rect, width)
    # NEW: square, diamond, right triangle and equilateral triangle
    elif shape["type"] == "square":
        rect = get_square_rect(start, end)
        if rect.width > 0:
            pygame.draw.rect(screen, color, rect, width)
    elif shape["type"] == "circle":
        center_x = (start[0] + end[0]) // 2
        center_y = (start[1] + end[1]) // 2
        radius = max(abs(start[0] - end[0]), abs(start[1] - end[1])) // 2
        if radius > 0:
            pygame.draw.circle(screen, color, (center_x, center_y), radius, width)
    elif shape["type"] == "diamond":
        points = get_diamond_points(start, end)
        if len(points) == 4:
            pygame.draw.polygon(screen, color, points, width)
    elif shape["type"] == "right_triangle":
        points = get_right_triangle_points(start, end)
        pygame.draw.polygon(screen, color, points, width)
    elif shape["type"] == "equilateral_triangle":
        points = get_equilateral_triangle_points(start, end)
        if len(points) == 3:
            pygame.draw.polygon(screen, color, points, width)

def draw_ui(screen, tool, color_mode, radius):
    font = pygame.font.SysFont("Verdana", 18)
    small_font = pygame.font.SysFont("Verdana", 14)

    pygame.draw.rect(screen, (30, 30, 30), pygame.Rect(8, 8, 365, 142))
    pygame.draw.rect(screen, (90, 90, 90), pygame.Rect(8, 8, 365, 142), 2)

    active_color = get_base_color(color_mode)
    tool_surface = font.render(f"Tool: {tool}", True, (255, 255, 255))
    color_surface = font.render(f"Color: {color_mode}", True, (255, 255, 255))
    size_surface = font.render(f"Size: {radius}", True, (255, 255, 255))

    screen.blit(tool_surface, (18, 15))
    screen.blit(color_surface, (18, 40))
    screen.blit(size_surface, (18, 65))
    pygame.draw.rect(screen, active_color, pygame.Rect(120, 42, 18, 18))

    # NEW: updated help panel with new shape shortcuts
    hints = [
        "P brush  E eraser  O circle  T rectangle  S square",
        "D diamond  Y right triangle  U equilateral triangle",
        "R/G/B color  Up/Down size  C clear",
    ]

    for index, hint in enumerate(hints):
        hint_surface = small_font.render(hint, True, (220, 220, 220))
        screen.blit(hint_surface, (18, 95 + index * 16))

def drawLineBetween(screen, index, start, end, width, color_mode):
    color = get_color(index, color_mode)
    
    dx = start[0] - end[0]
    dy = start[1] - end[1]
    iterations = max(abs(dx), abs(dy))

    if iterations == 0:
        pygame.draw.circle(screen, color, start, width)
        return
    
    for i in range(iterations):
        progress = 1.0 * i / iterations
        aprogress = 1 - progress
        x = int(aprogress * start[0] + progress * end[0])
        y = int(aprogress * start[1] + progress * end[1])
        pygame.draw.circle(screen, color, (x, y), width)

main()
