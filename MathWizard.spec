# -*- mode: python ; coding: utf-8 -*-
#
# Spec per l'eseguibile Windows (onefile), usato dal workflow
# .github/workflows/build-windows.yml sia per l'architettura 64-bit
# (MathWizard-windows.zip) sia per la 32-bit (MathWizard-windows-32bit.zip):
# PyInstaller produce un exe con la stessa bitness del Python in uso, quindi
# lo stesso spec vale per entrambe le architetture.
# - icona cercata in MathWizard.ico (radice repo, generata da graphics/misc/icon.png);
#   se assente si costruisce senza icona.
# - data/ e tutte le risorse (grafica, font, musica) incorporate nel onefile:
#   l'exe e' completamente autosufficiente (resource_path/_MEIPASS).
# - la versione (Proprieta' -> Dettagli) viene letta da math-wizard.py e scritta
#   come risorsa VERSIONINFO, cosi' resta una sola fonte di verita'.

import os
import re


def _read_app_version():
    """Versione unica, letta da math-wizard.py (self .version = "...")."""
    search_dirs = [os.getcwd()]
    spec_dir = globals().get('SPECPATH')
    if spec_dir:
        search_dirs.append(spec_dir)
    for base in search_dirs:
        candidate = os.path.join(base, 'math-wizard.py')
        if not os.path.exists(candidate):
            continue
        with open(candidate, encoding='utf-8') as fp:
            source = fp.read()
        match = re.search(r'self\s*\.\s*version\s*=\s*["\']([^"\']+)["\']', source)
        if match:
            return match.group(1)
    raise RuntimeError("Versione non trovata in math-wizard.py")


def _build_windows_version_file(version):
    """Genera il file VERSIONINFO (VSVersionInfo) da passare a EXE(version=...)."""
    try:
        from PyInstaller.utils.win32 import versioninfo as vi
    except Exception:
        return None
    numbers = [int(part) for part in re.findall(r'\d+', version)]
    while len(numbers) < 4:
        numbers.append(0)
    numbers = tuple(numbers[:4])
    info = vi.VSVersionInfo(
        ffi=vi.FixedFileInfo(
            filevers=numbers,
            prodvers=numbers,
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            vi.StringFileInfo([
                vi.StringTable('040904B0', [
                    vi.StringStruct('CompanyName', 'thefactor82'),
                    vi.StringStruct('FileDescription', 'Math Wizard'),
                    vi.StringStruct('FileVersion', version),
                    vi.StringStruct('InternalName', 'MathWizard'),
                    vi.StringStruct('OriginalFilename', 'MathWizard.exe'),
                    vi.StringStruct('ProductName', 'Math Wizard'),
                    vi.StringStruct('ProductVersion', version),
                ]),
            ]),
            vi.VarFileInfo([vi.VarStruct('Translation', [1033, 1200])]),
        ],
    )
    import tempfile
    version_file = os.path.join(tempfile.gettempdir(), 'MathWizard-version-%s.txt' % version)
    with open(version_file, 'w', encoding='utf-8') as fp:
        fp.write(str(info))
    return version_file


APP_VERSION = _read_app_version()
VERSION_FILE = _build_windows_version_file(APP_VERSION)

icon = []
for cand in ('MathWizard.ico', os.path.join('graphics', 'misc', 'icon.ico')):
    if os.path.exists(cand):
        icon = [cand]
        break

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
    version=VERSION_FILE,
    icon=icon,
)
