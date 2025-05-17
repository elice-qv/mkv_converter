import sys
import os
import subprocess
import time
import ffmpeg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QTextEdit, QProgressBar, QSpinBox, QListWidget,
                            QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

def find_ffmpeg():
    """Находит путь к ffmpeg в системе"""
    # Список возможных путей к ffmpeg
    possible_paths = [
        '/usr/local/bin/ffmpeg',  # Стандартный путь для Homebrew
        '/opt/homebrew/bin/ffmpeg',  # Путь для Apple Silicon
        '/usr/bin/ffmpeg',  # Системный путь
        os.path.expanduser('~/homebrew/bin/ffmpeg'),  # Пользовательский Homebrew
    ]
    
    # Проверяем каждый путь
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
            
    # Если не нашли в стандартных местах, пробуем через which
    try:
        result = subprocess.run(['which', 'ffmpeg'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        if result.stdout.strip():
            return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass
        
    return None

def check_ffmpeg():
    """Проверяет наличие ffmpeg и предлагает установить, если не найден"""
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("FFmpeg не найден")
        msg.setInformativeText("Для работы программы необходимо установить FFmpeg.\n\n"
                             "Установка на macOS:\n"
                             "1. Установите Homebrew (если еще не установлен):\n"
                             "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                             "2. Установите FFmpeg:\n"
                             "   brew install ffmpeg")
        msg.setWindowTitle("Ошибка")
        msg.exec()
        return None
    return ffmpeg_path

class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Проверяем наличие ffmpeg перед инициализацией интерфейса
        self.ffmpeg_path = check_ffmpeg()
        if not self.ffmpeg_path:
            sys.exit(1)
            
        self.setWindowTitle("MKV в MP4 Конвертер")
        self.setMinimumSize(800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Список файлов
        file_layout = QHBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        file_layout.addWidget(self.file_list)
        file_buttons_layout = QVBoxLayout()
        self.add_files_btn = QPushButton("Добавить файлы")
        self.add_files_btn.clicked.connect(self.add_files)
        self.remove_file_btn = QPushButton("Удалить выбранный")
        self.remove_file_btn.clicked.connect(self.remove_selected_file)
        self.clear_files_btn = QPushButton("Очистить список")
        self.clear_files_btn.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(self.add_files_btn)
        file_buttons_layout.addWidget(self.remove_file_btn)
        file_buttons_layout.addWidget(self.clear_files_btn)
        file_layout.addLayout(file_buttons_layout)
        layout.addLayout(file_layout)

        # Настройки качества
        quality_layout = QHBoxLayout()
        video_layout = QVBoxLayout()
        video_layout.addWidget(QLabel("Видео битрейт (Mbps):"))
        self.video_bitrate = QSpinBox()
        self.video_bitrate.setRange(1, 50)
        self.video_bitrate.setValue(8)
        video_layout.addWidget(self.video_bitrate)
        quality_layout.addLayout(video_layout)
        audio_layout = QVBoxLayout()
        audio_layout.addWidget(QLabel("Аудио битрейт (kbps):"))
        self.audio_bitrate = QSpinBox()
        self.audio_bitrate.setRange(64, 320)
        self.audio_bitrate.setValue(192)
        audio_layout.addWidget(self.audio_bitrate)
        quality_layout.addLayout(audio_layout)
        layout.addLayout(quality_layout)

        # Кнопка конвертации
        self.convert_btn = QPushButton("Конвертировать")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        # Прогресс
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Лог
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.input_files = []
        self.conversion_thread = None

    def add_files(self):
        try:
            file_names, _ = QFileDialog.getOpenFileNames(
                self,
                "Выберите MKV файлы",
                "",
                "MKV Files (*.mkv)"
            )
            if file_names:
                for file_name in file_names:
                    if file_name not in self.input_files:
                        self.input_files.append(file_name)
                        self.file_list.addItem(os.path.basename(file_name))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении файлов: {str(e)}")

    def remove_selected_file(self):
        try:
            current_row = self.file_list.currentRow()
            if current_row >= 0:
                self.file_list.takeItem(current_row)
                self.input_files.pop(current_row)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении файла: {str(e)}")

    def clear_files(self):
        try:
            self.file_list.clear()
            self.input_files.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при очистке списка: {str(e)}")

    def start_conversion(self):
        try:
            if not self.input_files:
                QMessageBox.warning(self, "Предупреждение", "Пожалуйста, добавьте файлы для конвертации")
                return
                
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Выберите папку для сохранения",
                ""
            )
            if not output_dir:
                return
                
            self.convert_btn.setEnabled(False)
            self.progress_bar.setRange(0, 0)
            self.conversion_thread = ConversionThread(
                self.input_files,
                output_dir,
                self.video_bitrate.value(),
                self.audio_bitrate.value(),
                self.ffmpeg_path
            )
            self.conversion_thread.progress.connect(self.update_log)
            self.conversion_thread.finished.connect(self.conversion_finished)
            self.conversion_thread.error.connect(self.conversion_error)
            self.conversion_thread.file_progress.connect(self.update_file_progress)
            self.conversion_thread.start()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске конвертации: {str(e)}")
            self.convert_btn.setEnabled(True)

    def update_log(self, message):
        try:
            self.log_text.append(message.strip())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении лога: {str(e)}")

    def update_file_progress(self, current, total):
        try:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении прогресса: {str(e)}")

    def conversion_finished(self):
        try:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.convert_btn.setEnabled(True)
            self.log_text.append("Конвертация всех файлов завершена успешно!")
            QMessageBox.information(self, "Успех", "Конвертация всех файлов завершена успешно!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при завершении конвертации: {str(e)}")

    def conversion_error(self, error_message):
        try:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.convert_btn.setEnabled(True)
            self.log_text.append(f"Ошибка: {error_message}")
            QMessageBox.critical(self, "Ошибка", error_message)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обработке ошибки конвертации: {str(e)}")

class ConversionThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    file_progress = pyqtSignal(int, int)

    def __init__(self, input_files, output_dir, video_bitrate, audio_bitrate, ffmpeg_path):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate
        self.ffmpeg_path = ffmpeg_path

    def run(self):
        try:
            total_files = len(self.input_files)
            for index, input_file in enumerate(self.input_files, 1):
                self.file_progress.emit(index, total_files)
                output_file = os.path.join(
                    self.output_dir,
                    os.path.splitext(os.path.basename(input_file))[0] + ".mp4"
                )
                # Формируем команду с универсальными параметрами
                cmd = [
                    self.ffmpeg_path,
                    "-y",  # overwrite output files
                    "-i", input_file,
                    "-c:v", "libx264",  # Универсальный видеокодек H.264
                    "-preset", "medium",  # Баланс между качеством и скоростью
                    "-crf", "23",  # Константа качества (18-28, чем меньше, тем лучше)
                    "-profile:v", "high",  # Профиль H.264
                    "-level", "4.0",  # Уровень совместимости
                    "-pix_fmt", "yuv420p",  # Цветовое пространство для совместимости
                    "-c:a", "aac",  # Аудиокодек AAC
                    "-b:a", f"{self.audio_bitrate}k",  # Битрейт аудио
                    "-ar", "48000",  # Частота дискретизации аудио
                    "-ac", "2",  # Количество аудиоканалов (стерео)
                    "-movflags", "+faststart",  # Оптимизация для веб-воспроизведения
                    output_file
                ]
                self.progress.emit(f"Запуск: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True
                )
                for line in process.stdout:
                    self.progress.emit(f"[{index}/{total_files}] {line.strip()}")
                process.wait()
                if process.returncode != 0:
                    self.error.emit(f"Ошибка при конвертации файла {os.path.basename(input_file)}")
                    return
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = ConverterApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Критическая ошибка", f"Произошла критическая ошибка: {str(e)}")
        sys.exit(1) 