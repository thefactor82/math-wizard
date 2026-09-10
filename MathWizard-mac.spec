# -*- mode: python ; coding: utf-8 -*-
#
# Spec per il pacchetto macOS (.app) in stile onedir-in-bundle
# (runtime + risorse dentro il bundle, avvio senza estrazione).
# Usato dal workflow .github/workflows/build-macos.yml per entrambe le
# architetture: l'architettura target arriva dalla variabile d'ambiente
# TARGET_ARCH (arm64 | x86_64), altrimenti si usa quella della macchina di
# build.
# - grafica, data/, fonts/ e music/ sono copiati dentro il bundle
#   (non compressi in un onefile: partenza immediata, niente estrazione
#   temporanea a ogni avvio). L'app e' completamente autosufficiente e
#   funziona anche sotto App Translocation (dati accanto all'app
#   inaccessibili).
# - icona MathWizard.icns generata nel workflow da graphics/misc/icon.png
#
# Nota: i data NON vengono esternizzati, stanno dentro il bundle in
# Contents/Frameworks (o Contents/Resources). Il check nel workflow li
# cerca con find invece di archive_viewer (che legge solo l'archivio
# interno dell'EXE onefile).

import os
import platform

target_arch = os.environ.get('TARGET_ARCH') or platform.machine()

a = Analysis(
    ['math-wizard.py'],
    pathex=[],
    binaries=[],
    datas=[('graphics', 'graphics'), ('data', 'data'), ('fonts', 'fonts'), ('music', 'music')],
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
        'CFBundleShortVersionString': '1.3.51',
        'CFBundleVersion': '1.3.51',
        'NSHighResolutionCapable': True,
    },
)