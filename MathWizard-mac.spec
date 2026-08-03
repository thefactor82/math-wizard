# -*- mode: python ; coding: utf-8 -*-
#
# Spec per il pacchetto macOS (.app). Usato dal workflow
# .github/workflows/build-macos.yml per entrambe le architetture:
# l'architettura target arriva dalla variabile d'ambiente TARGET_ARCH
# (arm64 | x86_64), altrimenti si usa quella della macchina di build.
# - grafica inclusa nel bundle (datas)
# - data/ copiata nel workflow in dist/MathWizard.app/Contents/MacOS/data
#   (il gioco la cerca accanto all'eseguibile: data_path())
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
    a.binaries,
    a.datas,
    [],
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

app = BUNDLE(
    exe,
    name='MathWizard.app',
    icon='MathWizard.icns',
    bundle_identifier='com.thefactor82.mathwizard',
    info_plist={
        'CFBundleShortVersionString': '1.0.19',
        'CFBundleVersion': '1.0.19',
        'NSHighResolutionCapable': True,
    },
)
