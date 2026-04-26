import os

import pygame


class MusicPlayer:
    # В плейлист будут добавлены только файлы с такими расширениями.
    SUPPORTED_EXTENSIONS = (".mp3", ".wav")

    def __init__(self, music_folder_name="music"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.music_folder = os.path.join(base_dir, music_folder_name)
        # playlist хранит имена файлов, а current_index указывает на текущий трек.
        self.playlist = []
        self.current_index = 0
        # Эти флаги описывают текущее состояние воспроизведения.
        self.is_playing = False
        self.is_paused = False
        # Этот флаг не даёт случайно переключить трек после ручной остановки или смены.
        self.ignore_track_end_event = False
        self.load_playlist()

    def load_playlist(self):
        # Каждый раз заново собираем плейлист из папки с музыкой.
        self.playlist = []

        if not os.path.isdir(self.music_folder):
            return

        for file_name in sorted(os.listdir(self.music_folder)):
            if file_name.lower().endswith(self.SUPPORTED_EXTENSIONS):
                self.playlist.append(file_name)

        # Если плейлист стал короче, индекс не должен выходить за его пределы.
        if self.current_index >= len(self.playlist):
            self.current_index = 0

    def has_tracks(self):
        return len(self.playlist) > 0

    def get_current_track_name(self):
        if not self.has_tracks():
            return "No tracks found"
        return self.playlist[self.current_index]

    def get_playlist_info(self):
        if not self.has_tracks():
            return "Playlist: 0 tracks"
        return f"Playlist: {self.current_index + 1}/{len(self.playlist)} tracks"

    def get_status(self):
        # Возвращает текстовый статус для отображения в интерфейсе.
        if not self.has_tracks():
            return "Add MP3 or WAV files to the music folder"
        if self.is_playing:
            return "Playing"
        if self.is_paused:
            return "Paused"
        return "Stopped"

    def get_position_text(self):
        # get_pos() возвращает позицию воспроизведения в миллисекундах.
        if not self.has_tracks() or (not self.is_playing and not self.is_paused):
            return "Position: 00:00"

        position_ms = pygame.mixer.music.get_pos()
        if position_ms < 0:
            return "Position: 00:00"

        # Переводим миллисекунды в формат MM:SS для вывода на экран.
        total_seconds = position_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"Position: {minutes:02d}:{seconds:02d}"

    def _load_current_track(self):
        # Внутренний метод, который загружает текущий трек в pygame.mixer.
        if not self.has_tracks():
            return False

        track_path = os.path.join(self.music_folder, self.playlist[self.current_index])
        pygame.mixer.music.load(track_path)
        return True

    def play(self):
        if not self.has_tracks():
            return

        if self.is_paused:
            # Продолжаем этот же трек с места паузы.
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
            self.ignore_track_end_event = False
            return

        if self._load_current_track():
            # Запускаем выбранный трек с самого начала.
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.ignore_track_end_event = False

    def stop(self):
        # Помечаем остановку как ручную, чтобы не сработал автопереход к следующему треку.
        self.ignore_track_end_event = True
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True

    def toggle_play_pause(self):
        # Один метод для клавиши P: если играет, ставим на паузу, иначе запускаем.
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def next_track(self):
        if not self.has_tracks():
            return

        # Переходим вперёд по кругу: после последнего трека снова идёт первый.
        self.ignore_track_end_event = True
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def prev_track(self):
        if not self.has_tracks():
            return

        # Отрицательный индекс даёт переход по кругу: с первого трека на последний.
        self.ignore_track_end_event = True
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play()

    def handle_track_end(self):
        # Вызывается из main.py, когда pygame сообщает об окончании трека.
        if not self.has_tracks():
            return

        if self.ignore_track_end_event:
            self.ignore_track_end_event = False
            return

        # Автоматически включаем следующий трек после естественного окончания текущего.
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()
