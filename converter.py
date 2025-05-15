import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QTextEdit, QProgressBar, QSpinBox, QListWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ConversionThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    file_progress = pyqtSignal(int, int)

    def __init__(self, input_files, output_dir, video_bitrate, audio_bitrate):
        super().__init__()
        self.input_files = input_files
        self.output_dir = output_dir
        self.video_bitrate = video_bitrate
        self.audio_bitrate = audio_bitrate

    def run(self):
        try:
            total_files = len(self.input_files)
            for index, input_file in enumerate(self.input_files, 1):
                self.file_progress.emit(index, total_files)
                output_file = os.path.join(
                    self.output_dir,
                    os.path.splitext(os.path.basename(input_file))[0] + ".mp4"
                )
                # Формируем команду как в терминале
                cmd = [
                    "ffmpeg",
                    "-y",  # overwrite output files
                    "-i", input_file,
                    "-c:v", "h264_videotoolbox",
                    "-b:v", f"{self.video_bitrate}M",
                    "-c:a", "aac",
                    "-b:a", f"{self.audio_bitrate}k",
                    "-movflags", "+faststart",
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

class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
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

    def remove_selected_file(self):
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
            self.input_files.pop(current_row)

    def clear_files(self):
        self.file_list.clear()
        self.input_files.clear()

    def start_conversion(self):
        if not self.input_files:
            self.log_text.append("Пожалуйста, добавьте файлы для конвертации")
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
            self.audio_bitrate.value()
        )
        self.conversion_thread.progress.connect(self.update_log)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.error.connect(self.conversion_error)
        self.conversion_thread.file_progress.connect(self.update_file_progress)
        self.conversion_thread.start()

    def update_log(self, message):
        self.log_text.append(message.strip())

    def update_file_progress(self, current, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

    def conversion_finished(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.convert_btn.setEnabled(True)
        self.log_text.append("Конвертация всех файлов завершена успешно!")

    def conversion_error(self, error_message):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.convert_btn.setEnabled(True)
        self.log_text.append(f"Ошибка: {error_message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConverterApp()
    window.show()
    sys.exit(app.exec()) 