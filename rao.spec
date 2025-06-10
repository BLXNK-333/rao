# rao.spec

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from pathlib import Path

block_cipher = None

# Относительные пути от текущей директории (т.е. проекта)
datas = [
    ('rao.ico', '.'),  # в корень
    ('src/frontend/icons', 'src/frontend/icons'),  # иконки
]

a = Analysis(
    ['main.py'],
    pathex=['.'],  # корень проекта
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='rao',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='rao.ico'
)
