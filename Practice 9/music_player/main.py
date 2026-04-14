import sys

import pygame

from player import MusicPlayer


WIDTH, HEIGHT = 900, 420
FPS = 30
TRACK_END_EVENT = pygame.USEREVENT + 1

BG_COLOR = (25, 25, 30)
TEXT_COLOR = (230, 230, 230)
ACCENT_COLOR = (100, 200, 150)
MUTED_COLOR = (150, 150, 150)


def draw_text_lines(screen, font, lines, color, start_x, start_y, line_gap):
    y = start_y
    for line in lines:
        text = font.render(line, True, color)
        screen.blit(text, (start_x, y))
        y += line_gap


def fit_text(font, text, max_width):
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    available_width = max_width - font.size(ellipsis)[0]
    trimmed_text = text

    while trimmed_text and font.size(trimmed_text)[0] > available_width:
        trimmed_text = trimmed_text[:-1]

    return trimmed_text.rstrip() + ellipsis


def main():
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(TRACK_END_EVENT)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Music Player")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("Arial", 30, bold=True)
    info_font = pygame.font.SysFont("Arial", 24)
    controls_font = pygame.font.SysFont("Courier New", 20)

    player = MusicPlayer("music")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == TRACK_END_EVENT:
                player.handle_track_end()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    player.toggle_play_pause()
                elif event.key == pygame.K_s:
                    player.stop()
                elif event.key == pygame.K_n:
                    player.next_track()
                elif event.key == pygame.K_b:
                    player.prev_track()
                elif event.key == pygame.K_q:
                    running = False

        screen.fill(BG_COLOR)

        track_name = fit_text(title_font, player.get_current_track_name(), WIDTH - 60)
        track_title = title_font.render(track_name, True, TEXT_COLOR)
        screen.blit(track_title, (30, 40))

        info_lines = [
            f"Status: {player.get_status()}",
            player.get_position_text(),
            player.get_playlist_info(),
        ]
        draw_text_lines(screen, info_font, info_lines, ACCENT_COLOR, 30, 100, 36)

        control_lines = [
            "Controls:",
            "P - Play / Pause",
            "S - Stop",
            "N - Next track",
            "B - Previous track",
            "Q - Quit",
        ]
        draw_text_lines(screen, controls_font, control_lines, MUTED_COLOR, 30, 250, 28)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
