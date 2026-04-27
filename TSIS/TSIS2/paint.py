from pathlib import Path

import pygame

from tools import (
    BACKGROUND_COLOR,
    BRUSH_SIZES,
    BUTTON_ACTIVE,
    BUTTON_COLOR,
    BUTTON_TEXT,
    CANVAS_COLOR,
    CANVAS_RECT,
    COLORS,
    PANEL_BORDER,
    TEXT_COLOR,
    TOOLBAR_COLOR,
    TOOLBAR_HEIGHT,
    TOOL_LABELS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    draw_freehand_segment,
    draw_shape,
    flood_fill,
    save_canvas,
)


BASE_DIR = Path(__file__).resolve().parent
SAVE_DIR = BASE_DIR / "saves"

TOOL_SHORTCUTS = {
    pygame.K_p: "pencil",
    pygame.K_l: "line",
    pygame.K_e: "eraser",
    pygame.K_f: "fill",
    pygame.K_t: "text",
    pygame.K_r: "rectangle",
    pygame.K_o: "circle",
    pygame.K_q: "square",
    pygame.K_y: "right_triangle",
    pygame.K_u: "equilateral_triangle",
    pygame.K_h: "rhombus",
}

SIZE_SHORTCUTS = {
    pygame.K_1: "small",
    pygame.K_2: "medium",
    pygame.K_3: "large",
}

TOOL_ORDER = [
    ("pencil", "Pencil", "P"),
    ("line", "Line", "L"),
    ("eraser", "Eraser", "E"),
    ("fill", "Fill", "F"),
    ("text", "Text", "T"),
    ("rectangle", "Rect", "R"),
    ("circle", "Circle", "O"),
    ("square", "Square", "Q"),
    ("right_triangle", "R-Tri", "Y"),
    ("equilateral_triangle", "E-Tri", "U"),
    ("rhombus", "Rhombus", "H"),
]

COLOR_ORDER = ["black", "red", "green", "blue", "yellow", "purple"]
SIZE_ORDER = ["small", "medium", "large"]
SHAPE_TOOLS = {
    "line",
    "rectangle",
    "circle",
    "square",
    "right_triangle",
    "equilateral_triangle",
    "rhombus",
}


def build_buttons():
    tool_buttons = []
    start_x = 20
    start_y = 18
    width = 102
    height = 30
    gap = 8

    for index, (tool, label, shortcut) in enumerate(TOOL_ORDER):
        row = index // 6
        column = index % 6
        rect = pygame.Rect(
            start_x + column * (width + gap),
            start_y + row * (height + gap),
            width,
            height,
        )
        tool_buttons.append(
            {
                "tool": tool,
                "label": label,
                "shortcut": shortcut,
                "rect": rect,
            }
        )

    size_buttons = []
    size_x = 690
    for index, size_name in enumerate(SIZE_ORDER):
        rect = pygame.Rect(size_x + index * 94, 18, 86, 30)
        size_buttons.append(
            {
                "size": size_name,
                "label": f"{index + 1} {size_name.title()}",
                "rect": rect,
            }
        )

    color_buttons = []
    color_x = 690
    for index, color_name in enumerate(COLOR_ORDER):
        rect = pygame.Rect(color_x + index * 48, 64, 36, 36)
        color_buttons.append(
            {
                "color": color_name,
                "rect": rect,
            }
        )

    save_button = {"rect": pygame.Rect(978, 18, 50, 30), "label": "Save"}
    clear_button = {"rect": pygame.Rect(1035, 18, 55, 30), "label": "Clear"}

    return tool_buttons, size_buttons, color_buttons, clear_button, save_button


def screen_to_canvas(screen_pos):
    return (screen_pos[0] - CANVAS_RECT.x, screen_pos[1] - CANVAS_RECT.y)


def clamp_screen_to_canvas(screen_pos):
    x = min(max(screen_pos[0], CANVAS_RECT.left), CANVAS_RECT.right - 1)
    y = min(max(screen_pos[1], CANVAS_RECT.top), CANVAS_RECT.bottom - 1)
    return x, y


def is_canvas_point(screen_pos):
    return CANVAS_RECT.collidepoint(screen_pos)


def draw_button(screen, font, rect, label, active=False):
    fill = BUTTON_ACTIVE if active else BUTTON_COLOR
    pygame.draw.rect(screen, fill, rect, border_radius=6)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 1, border_radius=6)
    text_surface = font.render(label, True, BUTTON_TEXT)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


def draw_toolbar(
    screen,
    font,
    small_font,
    tool_buttons,
    size_buttons,
    color_buttons,
    clear_button,
    save_button,
    active_tool,
    active_color_name,
    active_size_name,
    status_message,
    text_editing,
):
    pygame.draw.rect(screen, TOOLBAR_COLOR, pygame.Rect(0, 0, WINDOW_WIDTH, TOOLBAR_HEIGHT))
    pygame.draw.line(screen, PANEL_BORDER, (0, TOOLBAR_HEIGHT), (WINDOW_WIDTH, TOOLBAR_HEIGHT), 2)

    for button in tool_buttons:
        draw_button(
            screen,
            font,
            button["rect"],
            f"{button['shortcut']} {button['label']}",
            active=button["tool"] == active_tool,
        )

    for button in size_buttons:
        draw_button(
            screen,
            font,
            button["rect"],
            button["label"],
            active=button["size"] == active_size_name,
        )

    for button in color_buttons:
        color = COLORS[button["color"]]
        rect = button["rect"]
        pygame.draw.rect(screen, color, rect, border_radius=6)
        border_width = 3 if button["color"] == active_color_name else 1
        pygame.draw.rect(screen, PANEL_BORDER, rect, border_width, border_radius=6)

    draw_button(screen, font, save_button["rect"], save_button["label"])
    draw_button(screen, font, clear_button["rect"], clear_button["label"])

    title = font.render("TSIS2 Paint", True, TEXT_COLOR)
    info = small_font.render(
        f"Tool: {TOOL_LABELS[active_tool]}    Color: {active_color_name}    Size: {BRUSH_SIZES[active_size_name]} px",
        True,
        TEXT_COLOR,
    )
    status = small_font.render(status_message, True, TEXT_COLOR)
    hint_text = "Ctrl+S save   1/2/3 sizes   Click swatches for color"
    if text_editing:
        hint_text = "Text mode: type, Enter confirms, Escape cancels"
    hints = small_font.render(hint_text, True, TEXT_COLOR)

    screen.blit(title, (20, 108))
    screen.blit(info, (170, 110))
    screen.blit(status, (20, 130))
    screen.blit(hints, (635, 110))


def render_text_preview(canvas_display, font, text_position, text_buffer, color):
    preview_text = text_buffer if text_buffer else ""
    text_surface = font.render(preview_text, True, color)
    canvas_display.blit(text_surface, text_position)

    caret_x = text_position[0] + text_surface.get_width()
    top_y = text_position[1]
    bottom_y = top_y + font.get_height()
    pygame.draw.line(canvas_display, color, (caret_x, top_y), (caret_x, bottom_y), 1)


def commit_text(canvas, font, text_position, text_buffer, color):
    if text_position is None or not text_buffer:
        return
    text_surface = font.render(text_buffer, True, color)
    canvas.blit(text_surface, text_position)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("TSIS2 Paint")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Verdana", 15)
    small_font = pygame.font.SysFont("Verdana", 13)
    text_font = pygame.font.SysFont("Verdana", 24)

    canvas = pygame.Surface(CANVAS_RECT.size)
    canvas.fill(CANVAS_COLOR)

    tool_buttons, size_buttons, color_buttons, clear_button, save_button = build_buttons()

    active_tool = "pencil"
    active_color_name = "black"
    active_size_name = "medium"
    status_message = "Choose a tool, draw on the canvas, or press Ctrl+S to save."

    freehand_last = None
    shape_start = None
    shape_current = None
    dragging = False

    text_position = None
    text_buffer = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if text_position is not None:
                        text_position = None
                        text_buffer = ""
                        status_message = "Text entry cancelled."
                    else:
                        running = False
                    continue

                if event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                    file_path = save_canvas(canvas, SAVE_DIR)
                    status_message = f"Saved canvas to {file_path.name}"
                    continue

                if text_position is not None:
                    if event.key == pygame.K_RETURN:
                        commit_text(
                            canvas,
                            text_font,
                            text_position,
                            text_buffer,
                            COLORS[active_color_name],
                        )
                        status_message = "Text placed on canvas."
                        text_position = None
                        text_buffer = ""
                    elif event.key == pygame.K_BACKSPACE:
                        text_buffer = text_buffer[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        text_buffer += event.unicode
                    continue

                if event.key == pygame.K_c:
                    canvas.fill(CANVAS_COLOR)
                    status_message = "Canvas cleared."
                    continue

                if event.key in SIZE_SHORTCUTS:
                    active_size_name = SIZE_SHORTCUTS[event.key]
                    status_message = f"Brush size set to {BRUSH_SIZES[active_size_name]} px."
                    continue

                if event.key in TOOL_SHORTCUTS:
                    active_tool = TOOL_SHORTCUTS[event.key]
                    status_message = f"Tool changed to {TOOL_LABELS[active_tool]}."
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = event.pos

                if text_position is not None and is_canvas_point(click_pos) and active_tool == "text":
                    commit_text(
                        canvas,
                        text_font,
                        text_position,
                        text_buffer,
                        COLORS[active_color_name],
                    )
                    text_buffer = ""
                    text_position = None

                handled = False

                for button in tool_buttons:
                    if button["rect"].collidepoint(click_pos):
                        active_tool = button["tool"]
                        status_message = f"Tool changed to {TOOL_LABELS[active_tool]}."
                        handled = True
                        break

                if handled:
                    continue

                for button in size_buttons:
                    if button["rect"].collidepoint(click_pos):
                        active_size_name = button["size"]
                        status_message = f"Brush size set to {BRUSH_SIZES[active_size_name]} px."
                        handled = True
                        break

                if handled:
                    continue

                for button in color_buttons:
                    if button["rect"].collidepoint(click_pos):
                        active_color_name = button["color"]
                        status_message = f"Color changed to {active_color_name}."
                        handled = True
                        break

                if handled:
                    continue

                if clear_button["rect"].collidepoint(click_pos):
                    canvas.fill(CANVAS_COLOR)
                    text_position = None
                    text_buffer = ""
                    status_message = "Canvas cleared."
                    continue

                if save_button["rect"].collidepoint(click_pos):
                    file_path = save_canvas(canvas, SAVE_DIR)
                    status_message = f"Saved canvas to {file_path.name}"
                    continue

                if not is_canvas_point(click_pos):
                    continue

                local_pos = screen_to_canvas(click_pos)
                active_color = CANVAS_COLOR if active_tool == "eraser" else COLORS[active_color_name]
                active_width = BRUSH_SIZES[active_size_name]

                if active_tool == "fill":
                    pixels = flood_fill(canvas, local_pos, active_color)
                    status_message = f"Fill tool painted {pixels} pixels."
                elif active_tool == "text":
                    text_position = local_pos
                    text_buffer = ""
                    status_message = "Type text, then press Enter to place it."
                elif active_tool == "pencil" or active_tool == "eraser":
                    dragging = True
                    freehand_last = local_pos
                    draw_freehand_segment(canvas, active_color, active_width, local_pos, local_pos)
                else:
                    dragging = True
                    shape_start = local_pos
                    shape_current = local_pos

            if event.type == pygame.MOUSEMOTION and dragging:
                clamped = clamp_screen_to_canvas(event.pos)
                local_pos = screen_to_canvas(clamped)
                active_color = CANVAS_COLOR if active_tool == "eraser" else COLORS[active_color_name]
                active_width = BRUSH_SIZES[active_size_name]

                if active_tool == "pencil" or active_tool == "eraser":
                    draw_freehand_segment(canvas, active_color, active_width, freehand_last, local_pos)
                    freehand_last = local_pos
                elif active_tool in SHAPE_TOOLS:
                    shape_current = local_pos

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and active_tool in SHAPE_TOOLS and shape_start is not None and shape_current is not None:
                    active_color = COLORS[active_color_name]
                    active_width = BRUSH_SIZES[active_size_name]
                    draw_shape(canvas, active_tool, active_color, active_width, shape_start, shape_current)

                dragging = False
                freehand_last = None
                shape_start = None
                shape_current = None

        screen.fill(BACKGROUND_COLOR)

        canvas_display = canvas.copy()
        if dragging and active_tool in SHAPE_TOOLS and shape_start is not None and shape_current is not None:
            draw_shape(
                canvas_display,
                active_tool,
                COLORS[active_color_name],
                BRUSH_SIZES[active_size_name],
                shape_start,
                shape_current,
            )

        if text_position is not None:
            render_text_preview(
                canvas_display,
                text_font,
                text_position,
                text_buffer,
                COLORS[active_color_name],
            )

        pygame.draw.rect(screen, (245, 246, 249), CANVAS_RECT, border_radius=8)
        screen.blit(canvas_display, CANVAS_RECT.topleft)
        pygame.draw.rect(screen, PANEL_BORDER, CANVAS_RECT, 2, border_radius=8)

        mouse_pos = pygame.mouse.get_pos()
        if active_tool == "eraser" and is_canvas_point(mouse_pos):
            preview_radius = max(2, BRUSH_SIZES[active_size_name] // 2)
            pygame.draw.circle(screen, (255, 255, 255), mouse_pos, preview_radius + 1, 1)
            pygame.draw.circle(screen, PANEL_BORDER, mouse_pos, preview_radius, 1)

        draw_toolbar(
            screen,
            font,
            small_font,
            tool_buttons,
            size_buttons,
            color_buttons,
            clear_button,
            save_button,
            active_tool,
            active_color_name,
            active_size_name,
            status_message,
            text_position is not None,
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
