# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# openpyxl is dynamically imported by pandas only when read_excel/to_excel is called.
# PyInstaller's static analysis misses it entirely, so we force-collect everything.
openpyxl_datas, openpyxl_binaries, openpyxl_hiddenimports = collect_all('openpyxl')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=openpyxl_binaries,
    datas=openpyxl_datas,
    hiddenimports=(
        openpyxl_hiddenimports
        + collect_submodules('openpyxl')
        + [
            'openpyxl',
            'openpyxl.cell._writer',
            'openpyxl.styles.numbers',
            'openpyxl.styles.stylesheet',
            'openpyxl.worksheet._writer',
            'openpyxl.writer.excel',
        ]
    ),
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
    name='Camplife DataLoader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Camplife DataLoader',
)
