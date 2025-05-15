# MKV в MP4 Конвертер

Простое приложение для конвертации MKV файлов в MP4 формат с использованием ffmpeg. Конвертация mkv в mp4 без ограничений и бесплатно! Но придется повозиться с установкой 🙂 

<img width="912" alt="image" src="https://github.com/user-attachments/assets/ef56fd06-96b2-437e-80a9-c8a46dd39c0d" />


## Требования

- Python 3.8 или выше
- ffmpeg (установленный в системе)

# Установка


1. Установка ffmpeg и python
   ## Python
   ```bash
   https://www.python.org/ftp/python/3.13.3/python-3.13.3-macos11.pkg
   ```
   
   ## macOS
   В терминале:
   1. Установить brew (Альтернативный поставщик ПО)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
   2. Установить ffmpeg
   ```bash
   brew install ffmpeg create-dmg
   ```
   
   или
   
   Установщик ffmpeg:
   ```bash
   https://evermeet.cx/ffmpeg/ffmpeg-119458-g4e5523c985.7z
   ```
   _Рекомендую установить через brew_
   
   ## Windows
   
   ### Скачайте и установите ffmpeg с официального сайта
   ```bash
   https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
   ```
   ## Установите NSIS для создания установщика
   ```bash
   https://prdownloads.sourceforge.net/nsis/nsis-3.11-setup.exe?download
   ```

3. Установите зависимости Python:
   ```bash
   pip install -r requirements.txt
   ```

4. Запустите скрипт сборки:
   ```bash
   python build.py
   ```
   На windows после сборки появится .exe
   На macOS после сборки появится готовоая .app директория в папке dist. Перенесите приложение с иконкой в папку "Программы"

## Использование

1. Запустите приложение
2. В открывшемся окне:
   - Нажмите "Добавить файлы" для выбора MKV файлов
   - Настройте параметры качества (видео и аудио битрейт)
   - Нажмите "Конвертировать"
   - Следите за прогрессом в логе

## Особенности

- Использует аппаратное ускорение через VideoToolbox на macOS
- Поддерживает настройку битрейта видео и аудио
- Отображает прогресс конвертации в реальном времени
- Сохраняет оригинальное качество видео
- Создает MP4 файл с поддержкой быстрого старта
- Поддерживает конвертацию нескольких файлов в очереди 
