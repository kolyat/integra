# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
APP_NAME = 'setpwd'


a = Analysis(
    ['setpwd.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
