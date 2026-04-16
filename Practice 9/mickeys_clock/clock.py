import datetime # импортирует модуль datetime, который предоставляет классы для работы с датой и
# временем. В данном коде он используется для получения текущего времени, чтобы правильно
# отображать положение стрелок часов.
import os

import pygame

#
def scale_point(point, original_size, new_size):
    original_width, original_height = original_size
    new_width, new_height = new_size
    x, y = point

    scaled_x = round(x * new_width / original_width)
    scaled_y = round(y * new_height / original_height)
    return (scaled_x, scaled_y)


# функция для вычисления точки поворота относительно нижнего центра изображения. Она принимает
# размер изображения и смещение от нижнего края, и возвращает координаты точки поворота.
# Эта точка будет использоваться для вращения стрелок часов вокруг правильной оси.
def bottom_center_pivot(size, bottom_offset=0):
    width, height = size
    return (width // 2, height - bottom_offset)

# тут идут константы: размеры окна, цвета, имена файлов с изображениями, позиций микки и его рук,
# а также размеры и позиции для отрисовки часов и текста, если изображения не будут найдены. 
WIDTH, HEIGHT = 900, 700
FPS = 30
BACKGROUND_COLOR = (245, 245, 245)
TEXT_COLOR = (40, 40, 40)
ACCENT_COLOR = (220, 60, 60)

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
CLOCK_FACE_FILE = "clock_face.png"
MICKEY_FILE = "mickey.png"
LEFT_HAND_FILE = "left_hand.png"
RIGHT_HAND_FILE = "right_hand.png"

CLOCK_FACE_SIZE = (800, 600)
CLOCK_FACE_CENTER = (WIDTH // 2, HEIGHT // 2 + 20)

MICKEY_SIZE = (350, 350)
MICKEY_CENTER = (WIDTH // 2, HEIGHT // 2)

LEFT_HAND_SIZE = (50, 150)
LEFT_HAND_CENTER = (WIDTH // 2 + 4, HEIGHT // 2 + 5)
LEFT_HAND_PIVOT = bottom_center_pivot(LEFT_HAND_SIZE, bottom_offset=10)

RIGHT_HAND_SIZE = (100, 100)
RIGHT_HAND_CENTER = (WIDTH // 2 - 5, HEIGHT // 2 + 4)
RIGHT_HAND_PIVOT = bottom_center_pivot(RIGHT_HAND_SIZE, bottom_offset=10)

CENTER_DOT_POSITION = (WIDTH // 2, HEIGHT // 2)
TIME_TEXT_POSITION = (WIDTH // 2, HEIGHT - 50)

FALLBACK_CLOCK_RADIUS = 220
FALLBACK_MICKEY_HEAD_RADIUS = 80
FALLBACK_LEFT_HAND_LENGTH = 180
FALLBACK_RIGHT_HAND_LENGTH = 150


def load_image(file_name): # загружает изображение из папки images. Он принимает имя файла, формирует
    # полный путь к этому файлу и проверяет, существует ли он. Если файл существует, он загружает
    # его с помощью функции pygame.image.load() и возвращает объект изображения. Если файл не
    # найден, функция возвращает None.
    path = os.path.join(IMAGES_DIR, file_name)
    if os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    return None


def scale_image(image, size): # подгоняет картинку под нужный размер.
    if image is None:
        return None

    return pygame.transform.smoothscale(image, size) 
    # функция smoothscale() используется для изменения размера изображения с сохранением его качества.


def rotate_center(image, angle, center):
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_rect = rotated_image.get_rect(center=center)
    return rotated_image, rotated_rect


def rotate_around_pivot(image, angle, position, pivot):# делает поворот изображения вокруг такой опорной точки.
    image_rect = image.get_rect(topleft=(position[0] - pivot[0], position[1] - pivot[1]))
    offset = pygame.math.Vector2(position) - image_rect.center
    rotated_offset = offset.rotate(-angle)

    rotated_image = pygame.transform.rotate(image, angle)
    rotated_center = (position[0] - rotated_offset.x, position[1] - rotated_offset.y)
    rotated_rect = rotated_image.get_rect(center=rotated_center)
    return rotated_image, rotated_rect


class MickeyClock:
    def __init__(self):# загружаются фон часов, сам Микки и две руки.
        self.clock_face = scale_image(load_image(CLOCK_FACE_FILE), CLOCK_FACE_SIZE)
        self.mickey = scale_image(load_image(MICKEY_FILE), MICKEY_SIZE)
        self.left_hand = scale_image(load_image(LEFT_HAND_FILE), LEFT_HAND_SIZE)
        self.right_hand = scale_image(load_image(RIGHT_HAND_FILE), RIGHT_HAND_SIZE)

    def get_angles(self): # берется текущее время
        now = datetime.datetime.now()
        minutes = now.minute
        seconds = now.second

        minute_angle = -((minutes + seconds / 60) * 6)
        second_angle = -(seconds * 6) # для минутной стрелки: 360 градусов / 60 минут = 6 градусов
        # в минуту. Для секундной стрелки: 360 градусов / 60 секунд = 6 градусов в секунду.
        # Минус используется для корректного направления вращения стрелок.
        return minute_angle, second_angle, now

    def draw_background(self, screen): # рисует фон циферблата
        screen.fill(BACKGROUND_COLOR)

        if self.clock_face:
            face_rect = self.clock_face.get_rect(center=CLOCK_FACE_CENTER)
            screen.blit(self.clock_face, face_rect)
        else:
            pygame.draw.circle(screen, (230, 230, 230), CLOCK_FACE_CENTER, FALLBACK_CLOCK_RADIUS)
            pygame.draw.circle(screen, TEXT_COLOR, CLOCK_FACE_CENTER, FALLBACK_CLOCK_RADIUS, 4)

    def draw_mickey(self, screen): # рисует микки
        if self.mickey:
            mickey_rect = self.mickey.get_rect(center=MICKEY_CENTER)
            screen.blit(self.mickey, mickey_rect)
        else:
            pygame.draw.circle(screen, (30, 30, 30), MICKEY_CENTER, FALLBACK_MICKEY_HEAD_RADIUS)
            pygame.draw.circle(screen, (30, 30, 30), (MICKEY_CENTER[0] - 65, MICKEY_CENTER[1] - 70), 35)
            pygame.draw.circle(screen, (30, 30, 30), (MICKEY_CENTER[0] + 65, MICKEY_CENTER[1] - 70), 35)

    def draw_hand(self, screen, image, angle, center, pivot, length, width, color):
        # показывает минуты и секунды дл рук микки. Если изображения для рук не найдены,
        # то рисует простые линии от центра часов до рассчитанных конечных точек, используя углы для определения направления.
        if image:
            rotated_image, rotated_rect = rotate_around_pivot(image, angle, center, pivot)
            screen.blit(rotated_image, rotated_rect)
            return

        direction = pygame.math.Vector2(0, -1).rotate(-angle)
        end_x = int(center[0] + length * direction.x)
        end_y = int(center[1] + length * direction.y)
        pygame.draw.line(screen, color, center, (end_x, end_y), width)

    def draw_time_text(self, screen, now): # пишет врея в формате MM:SS внизу экрана.
        font = pygame.font.SysFont("Arial", 28, bold=True)
        time_text = font.render(f"{now.minute:02d}:{now.second:02d}", True, TEXT_COLOR)
        time_rect = time_text.get_rect(center=TIME_TEXT_POSITION)
        screen.blit(time_text, time_rect)

    def draw_missing_images_hint(self, screen):
        # показывает подсказку, если каких-то PNG нет.
        if all([self.clock_face, self.mickey, self.left_hand, self.right_hand]):
            return

        font = pygame.font.SysFont("Arial", 20)
        hint = font.render("Add PNG images to Practice10/mickeys_clock/images", True, ACCENT_COLOR)
        hint_rect = hint.get_rect(center=(WIDTH // 2, 40))
        screen.blit(hint, hint_rect)

    def draw(self, screen):
        # сначала вычисляются углы для минутной и секундной стрелок на основе текущего времени,
        # полученного с помощью метода get_angles(). Затем последовательно вызываются методы для
        # отрисовки фона, Микки, стрелок, центральной точки и текста с временем.
        # Если изображения для стрелок не найдены, вместо них рисуются простые линии.
        minute_angle, second_angle, now = self.get_angles()

        self.draw_background(screen)
        self.draw_mickey(screen)
        self.draw_hand(
            screen,
            self.right_hand,
            minute_angle,
            RIGHT_HAND_CENTER,
            RIGHT_HAND_PIVOT,
            FALLBACK_RIGHT_HAND_LENGTH,
            10,
            (40, 40, 40),
        )
        self.draw_hand(
            screen,
            self.left_hand,
            second_angle,
            LEFT_HAND_CENTER,
            LEFT_HAND_PIVOT,
            FALLBACK_LEFT_HAND_LENGTH,
            6,
            ACCENT_COLOR,
        )
        pygame.draw.circle(screen, TEXT_COLOR, CENTER_DOT_POSITION, 8)
        self.draw_time_text(screen, now)
        self.draw_missing_images_hint(screen)
