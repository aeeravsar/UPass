#!/usr/bin/env python3
"""
PyInstaller runtime hook to set up GI typelib path for bundled typelibs
"""

import os
import sys

# Set up GI_TYPELIB_PATH for bundled typelibs
if hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    typelib_path = os.path.join(sys._MEIPASS, 'gi_typelibs')
    if os.path.exists(typelib_path):
        gi_typelib_path = os.environ.get('GI_TYPELIB_PATH', '')
        if gi_typelib_path:
            os.environ['GI_TYPELIB_PATH'] = f"{typelib_path}:{gi_typelib_path}"
        else:
            os.environ['GI_TYPELIB_PATH'] = typelib_path