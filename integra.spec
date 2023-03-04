# -*- mode: python ; coding: utf-8 -*-
from kivy.tools.packaging import pyinstaller_hooks
from kivy_deps import sdl2, glew


block_cipher = None
APP_NAME = 'integra'
ICON = ['media\\integra.ico']
DATAS = [
    ('media', 'media'),
    ('*.kv', '.'),
    ('LICENSE', '.'),
]


a = Analysis(
    ['integra.py'],
    pathex=[],
    datas=DATAS,
    hookspath=pyinstaller_hooks.hookspath(),
    hooksconfig={},
    runtime_hooks=pyinstaller_hooks.runtime_hooks(),
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    **pyinstaller_hooks.get_deps_minimal(
        audio=None,
        camera=None,
        clipboard=None,
        image=True,
        spelling=None,
        text=True,
        video=None,
        window=True
    )
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

print('* * * * * SCRIPTS * * * * *')
for f in a.scripts:
    print(f)
print('* * * * * BINARIES * * * * *')
for f in a.binaries:
    print(f)
print('* * * * * ZIPFILES * * * * *')
for f in a.zipfiles:
    print(f)
print('* * * * * DATAS * * * * *')
for f in a.datas:
    print(f)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)
