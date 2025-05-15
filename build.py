import os
import platform
import subprocess
import sys

def build_app():
    system = platform.system()
    
    # Общие параметры для PyInstaller
    pyinstaller_args = [
        '--name=MKV2MP4Converter',
        '--windowed',  # Не показывать консоль
        '--onefile',   # Создать один исполняемый файл
        '--clean',     # Очистить кэш
        '--noconfirm', # Не спрашивать подтверждения
        '--add-data=README.md:.',  # Добавить README
    ]

    if system == 'Darwin':  # macOS
        # Создаем .app
        subprocess.run(['pyinstaller'] + pyinstaller_args + ['converter.py'])
        
        app_path = 'dist/MKV2MP4Converter.app'
        
        # Создаем .pkg
        pkg_name = 'MKV2MP4Converter.pkg'
        
        # Создаем временный файл для productbuild
        component_plist = """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <array>
            <dict>
                <key>BundleIsRelocatable</key>
                <false/>
                <key>BundleIsVersionChecked</key>
                <true/>
                <key>BundleOverwriteAction</key>
                <string>upgrade</string>
                <key>RootRelativeBundlePath</key>
                <string>Applications/MKV2MP4Converter.app</string>
            </dict>
        </array>
        </plist>
        """
        
        with open('component.plist', 'w') as f:
            f.write(component_plist)
            
        # Создаем .pkg
        subprocess.run([
            'productbuild',
            '--component', app_path, '/Applications',
            '--product', 'component.plist',
            pkg_name
        ])
        
        # Удаляем временные файлы
        os.remove('component.plist')
        
        print(f"Создан {pkg_name}")
        
    elif system == 'Windows':
        # Создаем .exe
        subprocess.run(['pyinstaller'] + pyinstaller_args + ['converter.py'])
        
        # Создаем установщик с помощью NSIS
        nsis_script = """
        !include "MUI2.nsh"
        
        Name "MKV2MP4 Converter"
        OutFile "MKV2MP4Converter_Setup.exe"
        InstallDir "$PROGRAMFILES\\MKV2MP4Converter"
        
        !insertmacro MUI_PAGE_WELCOME
        !insertmacro MUI_PAGE_DIRECTORY
        !insertmacro MUI_PAGE_INSTFILES
        !insertmacro MUI_PAGE_FINISH
        
        !insertmacro MUI_UNPAGE_CONFIRM
        !insertmacro MUI_UNPAGE_INSTFILES
        
        !insertmacro MUI_LANGUAGE "Russian"
        
        Section "Install"
            SetOutPath "$INSTDIR"
            File "dist\\MKV2MP4Converter.exe"
            File "README.md"
            
            CreateDirectory "$SMPROGRAMS\\MKV2MP4Converter"
            CreateShortcut "$SMPROGRAMS\\MKV2MP4Converter\\MKV2MP4Converter.lnk" "$INSTDIR\\MKV2MP4Converter.exe"
            CreateShortcut "$DESKTOP\\MKV2MP4Converter.lnk" "$INSTDIR\\MKV2MP4Converter.exe"
            
            WriteUninstaller "$INSTDIR\\uninstall.exe"
            
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MKV2MP4Converter" \
                            "DisplayName" "MKV2MP4 Converter"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MKV2MP4Converter" \
                            "UninstallString" "$INSTDIR\\uninstall.exe"
        SectionEnd
        
        Section "Uninstall"
            Delete "$INSTDIR\\MKV2MP4Converter.exe"
            Delete "$INSTDIR\\README.md"
            Delete "$INSTDIR\\uninstall.exe"
            
            Delete "$SMPROGRAMS\\MKV2MP4Converter\\MKV2MP4Converter.lnk"
            RMDir "$SMPROGRAMS\\MKV2MP4Converter"
            Delete "$DESKTOP\\MKV2MP4Converter.lnk"
            
            RMDir "$INSTDIR"
            
            DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MKV2MP4Converter"
        SectionEnd
        """
        
        with open('installer.nsi', 'w', encoding='utf-8') as f:
            f.write(nsis_script)
            
        subprocess.run(['makensis', 'installer.nsi'])
        print("Создан MKV2MP4Converter_Setup.exe")
        
    else:
        print(f"Неподдерживаемая операционная система: {system}")

if __name__ == '__main__':
    build_app() 