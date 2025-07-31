#!/usr/bin/env python3
"""
UPass Server Version Management
Reads version from root VERSION file
"""

import os

def get_version():
    """Get the current UPass version from root VERSION file"""
    try:
        version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
        with open(version_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"

def get_version_info():
    """Get detailed version information"""
    version = get_version()
    try:
        parts = version.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        return {
            'version': version,
            'major': major,
            'minor': minor,
            'patch': patch
        }
    except (ValueError, IndexError):
        return {
            'version': version,
            'major': 0,
            'minor': 0,
            'patch': 0
        }

# Version constants
__version__ = get_version()
VERSION = __version__

if __name__ == '__main__':
    print(f"UPass Server v{get_version()}")