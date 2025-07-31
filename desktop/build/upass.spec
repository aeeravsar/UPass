# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get project root (go up one level from build directory)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

# Collect all CLI and GUI modules
cli_path = os.path.join(project_root, 'cli')
gui_path = os.path.join(project_root, 'gui')

# Data files to include
datas = [
    (os.path.join(project_root, 'icon.png'), '.'),
    (os.path.join(gui_path, 'theme.css'), 'gui'),
    (os.path.join(gui_path, 'icons'), 'gui/icons'),
    (cli_path, 'cli'),
    (gui_path, 'gui'),
]

# Add GI typelib files for Linux
import sys
if sys.platform.startswith('linux'):
    import subprocess
    try:
        # Find GI typelib directory and bundle ALL typelib files
        gi_typelib_path = subprocess.check_output(['pkg-config', '--variable=typelibdir', 'gobject-introspection-1.0']).decode().strip()
        if os.path.exists(gi_typelib_path):
            # Bundle entire typelib directory
            datas.append((gi_typelib_path, 'gi_typelibs'))
    except:
        pass

# Hidden imports for dynamically loaded modules
hiddenimports = [
    'gi',
    'gi.repository.Gtk',
    'gi.repository.GLib',
    'gi.repository.Gdk',
    'gi.repository.GObject',
    'gi.repository.Gio',
    'gi.repository.Atk',
    'gi.repository.cairo',
    'gi.repository.Pango',
    'gi.repository.GdkPixbuf',
    'gi.repository.xlib',
    'gi._constants',
    'gi._gi',
    'nacl.signing',
    'nacl.secret', 
    'nacl.pwhash',
    'nacl.utils',
    'nacl.c.sodium',
    'requests',
    'cryptography',
    'cryptography.hazmat.primitives.ciphers.aead',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.kdf.pbkdf2',
    'pyperclip',
    'pickle',
    'base64',
    'hmac',
    'hashlib',
    'pathlib',
    'argparse',
    'importlib.util',
]

# Block list for unused modules to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'PIL',
    'cv2',
    'PyQt5',        # Exclude Qt frameworks that get auto-included
    'PyQt6',
    'PySide2',
    'PySide6',
    'qt5',
    'qt6',
]

# Essential libraries whitelist for portable builds
def filter_binaries(binaries):
    """Include only essential libraries to reduce build size while maintaining portability"""
    if not sys.platform.startswith('linux'):
        return binaries
    
    filtered = []
    included_count = 0
    included_size = 0
    
    # Essential library patterns (whitelist approach)
    essential_patterns = [
        # Core GTK/GUI libraries
        'libgtk-3.so',
        'libgdk-3.so', 
        'libglib-2.0.so',
        'libgobject-2.0.so',
        'libgio-2.0.so',
        'libgmodule-2.0.so',
        'libgthread-2.0.so',
        'libpango-1.0.so',
        'libpangocairo-1.0.so',
        'libpangoft2-1.0.so',
        'libcairo.so',
        'libcairo-gobject.so',
        'libgdk_pixbuf-2.0.so',
        'libatk-1.0.so',
        'librsvg-2.so',
        
        # Essential system libraries
        'libssl.so',
        'libcrypto.so',
        'libffi.so',
        'libz.so',
        'libbz2.so',
        'liblzma.so',
        'libexpat.so',
        'libfontconfig.so',
        'libfreetype.so',
        'libharfbuzz.so',
        'libpixman-1.so',
        'libpng16.so',
        'libjpeg.so',
        'libX11.so',
        'libXext.so',
        'libXrender.so',
        'libXi.so',
        'libXfixes.so',
        'libXcomposite.so',
        'libXdamage.so',
        'libXrandr.so',
        'libXcursor.so',
        'libXinerama.so',
        'libXss.so',
        'libxcb.so',
        'libxcb-render.so',
        'libxcb-shm.so',
        
        # Python runtime essentials
        'libpython3.',
        
        # Application-specific libraries
        'cryptography/',
        'nacl/',
        'bcrypt/',
        '_cffi_backend.',
        '_brotli.',
        
        # Essential Python modules
        'lib-dynload/_asyncio.',
        'lib-dynload/_bisect.',
        'lib-dynload/_blake2.',
        'lib-dynload/_bz2.',
        'lib-dynload/_contextvars.',
        'lib-dynload/_csv.',
        'lib-dynload/_ctypes.',
        'lib-dynload/_datetime.',
        'lib-dynload/_decimal.',
        'lib-dynload/_hashlib.',
        'lib-dynload/_heapq.',
        'lib-dynload/_json.',
        'lib-dynload/_lzma.',
        'lib-dynload/_md5.',
        'lib-dynload/_multiprocessing.',
        'lib-dynload/_opcode.',
        'lib-dynload/_pickle.',
        'lib-dynload/_posixshmem.',
        'lib-dynload/_posixsubprocess.',
        'lib-dynload/_queue.',
        'lib-dynload/_random.',
        'lib-dynload/_sha1.',
        'lib-dynload/_sha256.',
        'lib-dynload/_sha512.',
        'lib-dynload/_socket.',
        'lib-dynload/_ssl.',
        'lib-dynload/_struct.',
        'lib-dynload/array.',
        'lib-dynload/binascii.',
        'lib-dynload/fcntl.',
        'lib-dynload/grp.',
        'lib-dynload/math.',
        'lib-dynload/mmap.',
        'lib-dynload/select.',
        'lib-dynload/termios.',
        'lib-dynload/time.',
        'lib-dynload/unicodedata.',
        'lib-dynload/zlib.',
        
        # GI bindings
        'gi/_gi.',
        'gi/_gi_cairo.',
        
        # Essential GIO modules (minimal set)
        'gio_modules/libdconfsettings.so',
        'gio_modules/libgiognomeproxy.so',
        
        # GDK pixbuf loaders (essential for image loading)
        'lib/gdk-pixbuf/',
        'libpixbufloader',
        
        # Additional GTK essentials  
        'loaders.cache',
        
        # Application files
        'cli/',
        'gui/',
        'PYZ.pyz',
    ]
    
    for name, path, typecode in binaries:
        # Check if this binary matches any essential pattern
        is_essential = any(pattern in name for pattern in essential_patterns)
        
        if is_essential:
            filtered.append((name, path, typecode))
            included_count += 1
            try:
                included_size += os.path.getsize(path) if os.path.exists(path) else 0
            except:
                pass
    
    print(f"Included {included_count} essential libraries ({included_size / 1024 / 1024:.1f}MB)")
    return filtered

a = Analysis(
    [os.path.join(project_root, 'upass.py')],
    pathex=[project_root, cli_path, gui_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={
        "gi": {
            "icons": ["Adwaita"],
            "themes": ["Adwaita"], 
            "languages": ["en"],
        },
    },
    runtime_hooks=[os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'pyi_rth_gi_typelibs.py')] if sys.platform.startswith('linux') else [],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out theme files on Linux to reduce size
if sys.platform.startswith('linux'):
    a.binaries = filter_binaries(a.binaries)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='upass',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.png'),
)