# -*- mode: python ; coding: utf-8 -*-
#
# Spec per l'eseguibile Windows (onefile).
# Usata anche dal workflow .github/workflows/build-windows.yml.
# - icona cercata in MathWizard.ico (radice repo, generata da graphics/misc/icon.png);
#   se assente si costruisce senza icona.
# - data/ copiata dal workflow accanto all'exe (data_path()).

import os

icon = []
for cand in ('MathWizard.ico', os.path.join('graphics', 'misc', 'icon.ico')):
    if os.path.exists(cand):
        icon = [cand]
        break

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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
