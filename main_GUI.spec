# Source - https://stackoverflow.com/a
# Posted by user32882
# Retrieved 2025-12-24, License - CC BY-SA 4.0

# -*- mode: python -*-

block_cipher = None
import glob, os
rasterio_imports_paths = glob.glob(r'D:\Coding\Sonarlab-Mosaic\.venv\Lib\site-packages\rasterio\*.py')
rasterio_imports = ['rasterio._shim']

for item in rasterio_imports_paths:
    current_module_filename = os.path.split(item)[-1]
    current_module_filename = 'rasterio.'+ current_module_filename.replace('.py', '')
    rasterio_imports.append(current_module_filename)

# from pyproj import datadir
# proj_dir = datadir.get_data_dir()

a = Analysis(['main_GUI.py'],
             pathex=['Dist'],
             binaries=[],
             datas=[],
             hiddenimports=rasterio_imports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='sonarmosaic',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          icon='icon.ico',
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Sonar Mosaic')
