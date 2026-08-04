# -*- mode: python ; coding: utf-8 -*-
#
# Spec per il pacchetto macOS (.app) in modalita' ONEDIR (COLLECT + BUNDLE),
# il pattern supportato da PyInstaller per i bundle Finder: il bundle
# "onefile" (EXE autonomo dentro Contents/MacOS) causa crash all'avvio da
# Finder (estrazione in tmp + firma dei file estratti + ambiente ridotto).
# Usato dal workflow .github/workflows/build-macos.yml per entrambe le
# architetture: l'architettura target arriva dalla variabile d'ambiente
# TARGET_ARCH (arm64 | x86_64), altrimenti si usa quella della macchina di
# build.
# Layout del bundle prodotto da PyInstaller 6.15:
#   Contents/MacOS/MathWizard     -> eseguibile (bootloader)
#   Contents/Frameworks/          -> binari (sys._MEIPASS)
#   Contents/Resources/           -> dati (grafica), cross-link in Frameworks
# - data/ e profili NON sono nel bundle: il gioco (app_base_dir) li cerca
#   nella cartella che contiene MathWizard.app, e il workflow li copia li'.
# - icona MathWizard.icns generata nel workflow da graphics/misc/icon.png

import os
import platform

target_arch = os.environ.get('TARGET_ARCH') or platform.machine()

a = Analysis(
    ['math-wizard.py'],
    pathex=[],
    binaries=[],
    datas=[('graphics', 'graphics')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MathWizard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='MathWizard',
)

app = BUNDLE(
    coll,
    name='MathWizard.app',
    icon='MathWizard.icns',
    bundle_identifier='com.thefactor82.mathwizard',
    info_plist={
        'CFBundleShortVersionString': '1.0.20',
        'CFBundleVersion': '1.0.20',
        'NSHighResolutionCapable': True,
    },
)
