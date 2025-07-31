#!/usr/bin/env python3
"""
UPass GTK GUI - Zero-knowledge password manager
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os
import argparse

# Add current directory for GUI imports
sys.path.insert(0, os.path.dirname(__file__))

from windows import MainWindow

# Add parent directory for version import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from version import get_version


class UPassApplication(Gtk.Application):
    """Main GTK application"""
    
    def __init__(self, server_url=None):
        super().__init__(application_id="org.upass.gui")
        self.server_url = server_url
        
        # Connect signals
        self.connect("activate", self.on_activate)
    
    def on_activate(self, app):
        """Handle application activation"""
        # Force dark theme preference
        self._setup_dark_theme()
        
        # Set default icon for the application
        self._set_default_icon()
        
        # Create main window with server URL
        window = MainWindow(app, server_url=self.server_url)
        window.present()
    
    def _setup_dark_theme(self):
        """Force GTK to prefer dark theme variants"""
        try:
            settings = Gtk.Settings.get_default()
            # Force dark theme preference (works better on Windows)
            settings.set_property("gtk-application-prefer-dark-theme", True)
            settings.set_property("gtk-theme-name", "Adwaita-dark")
        except Exception as e:
            print(f"Warning: Could not set dark theme preference: {e}")
    
    def _set_default_icon(self):
        """Set default application icon"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'icon.png')
            if os.path.exists(icon_path):
                Gtk.Window.set_default_icon_from_file(icon_path)
        except Exception as e:
            print(f"Warning: Could not load default icon: {e}")


def gui_main():
    """GUI main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=f"UPass GUI v{get_version()} - Zero-knowledge password manager"
    )
    parser.add_argument(
        '--server', '-s',
        help='UPass server URL (default: https://server.upass.ch)',
        default=None
    )
    args, remaining = parser.parse_known_args()
    
    # Check for required dependencies
    try:
        import nacl.signing
        import nacl.secret
        import nacl.pwhash
        import requests
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install required packages:")
        print("pip install pynacl requests pygobject")
        return 1
    
    # Create and run application with server URL
    app = UPassApplication(server_url=args.server)
    return app.run([sys.argv[0]] + remaining)


if __name__ == '__main__':
    sys.exit(gui_main())