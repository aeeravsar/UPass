import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk
import sys
import os
import threading

# Add CLI path for importing CLI modules
cli_path = os.path.join(os.path.dirname(__file__), '..', '..', 'cli')
if cli_path not in sys.path:
    sys.path.insert(0, cli_path)

from commands import UPassSession
from utils import validate_username


class LoginWindow(Gtk.Box):
    """Modern Login/Register widget"""
    
    def __init__(self, login_callback, session, initial_server_url=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.login_callback = login_callback
        self.session = session
        self.initial_server_url = initial_server_url
        self.is_register_mode = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup modern login UI"""
        # Background
        self.get_style_context().add_class("vault-container")
        
        # Center container
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center_box.set_halign(Gtk.Align.CENTER)
        center_box.set_valign(Gtk.Align.CENTER)
        self.pack_start(center_box, True, True, 0)
        
        # Login card
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.card.get_style_context().add_class("login-card")
        self.card.set_size_request(400, -1)
        center_box.pack_start(self.card, False, False, 0)
        
        # Header section
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header_box.set_halign(Gtk.Align.CENTER)
        self.card.pack_start(header_box, False, False, 0)
        
        # Title
        self.title_label = Gtk.Label("Welcome to UPass")
        self.title_label.get_style_context().add_class("login-title")
        header_box.pack_start(self.title_label, False, False, 0)
        
        # Subtitle
        self.subtitle_label = Gtk.Label("Zero-knowledge password manager")
        self.subtitle_label.get_style_context().add_class("login-subtitle")
        header_box.pack_start(self.subtitle_label, False, False, 0)
        
        # Form container
        self.form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.card.pack_start(self.form_box, False, False, 0)
        
        # Server field
        server_label = Gtk.Label("Server")
        server_label.set_halign(Gtk.Align.START)
        server_label.set_margin_left(4)
        self.form_box.pack_start(server_label, False, False, 0)
        
        self.server_entry = Gtk.Entry()
        self.server_entry.set_placeholder_text("server.upass.ch")
        self.server_entry.get_style_context().add_class("modern-entry")
        self.server_entry.connect("activate", lambda w: self.vault_entry.grab_focus())
        # Set initial server URL - strip https:// for cleaner display
        if self.initial_server_url:
            display_url = self.initial_server_url
            if display_url.startswith('https://'):
                display_url = display_url[8:]
            self.server_entry.set_text(display_url)
        else:
            self.server_entry.set_text("server.upass.ch")
        self.form_box.pack_start(self.server_entry, False, False, 0)
        
        # Vault name field
        vault_label = Gtk.Label("Vault Name")
        vault_label.set_halign(Gtk.Align.START)
        vault_label.set_margin_left(4)
        self.form_box.pack_start(vault_label, False, False, 0)
        
        self.vault_entry = Gtk.Entry()
        self.vault_entry.set_placeholder_text("Enter your vault name")
        self.vault_entry.get_style_context().add_class("modern-entry")
        self.vault_entry.connect("activate", lambda w: self.password_entry.grab_focus())
        self.form_box.pack_start(self.vault_entry, False, False, 0)
        
        # Password field
        password_label = Gtk.Label("Master Password")
        password_label.set_halign(Gtk.Align.START)
        password_label.set_margin_left(4)
        self.form_box.pack_start(password_label, False, False, 0)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Enter your master password")
        self.password_entry.set_visibility(False)
        self.password_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.password_entry.get_style_context().add_class("modern-entry")
        self.password_entry.connect("activate", lambda w: self._on_main_button_clicked(None))
        self.form_box.pack_start(self.password_entry, False, False, 0)
        
        # Confirm password field (for registration) - initially hidden
        self.confirm_label = Gtk.Label("Confirm Password")
        self.confirm_label.set_halign(Gtk.Align.START)
        self.confirm_label.set_margin_left(4)
        self.confirm_label.set_no_show_all(True)  # Prevent show_all() from showing this
        self.form_box.pack_start(self.confirm_label, False, False, 0)
        
        self.confirm_entry = Gtk.Entry()
        self.confirm_entry.set_placeholder_text("Confirm your master password")
        self.confirm_entry.set_visibility(False)
        self.confirm_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.confirm_entry.get_style_context().add_class("modern-entry")
        self.confirm_entry.set_no_show_all(True)  # Prevent show_all() from showing this
        self.confirm_entry.connect("activate", lambda w: self._on_main_button_clicked(None))
        self.form_box.pack_start(self.confirm_entry, False, False, 0)
        
        # Error label
        self.error_label = Gtk.Label()
        self.error_label.get_style_context().add_class("error-text")
        self.error_label.set_line_wrap(True)
        self.error_label.set_max_width_chars(50)
        self.error_label.set_justify(Gtk.Justification.CENTER)
        self.form_box.pack_start(self.error_label, False, False, 0)
        
        # Button container
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        button_box.set_margin_top(8)
        self.form_box.pack_start(button_box, False, False, 0)
        
        # Main action button
        self.main_button = Gtk.Button("Open Vault")
        self.main_button.get_style_context().add_class("primary-button")
        self.main_button.set_size_request(-1, 48)
        self.main_button.connect("clicked", self._on_main_button_clicked)
        button_box.pack_start(self.main_button, False, False, 0)
        
        # Mode toggle button
        self.mode_button = Gtk.Button("Create New Vault")
        self.mode_button.get_style_context().add_class("secondary-button")
        self.mode_button.set_size_request(-1, 40)
        self.mode_button.connect("clicked", self._toggle_mode)
        button_box.pack_start(self.mode_button, False, False, 0)
        
        # Progress spinner (hidden by default)
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(24, 24)
        self.spinner.set_halign(Gtk.Align.CENTER)
        button_box.pack_start(self.spinner, False, False, 0)
        
        # Initialize state - MUST be in login mode by default
        self.is_register_mode = False
        
        # Hide confirm fields explicitly 
        self.confirm_label.set_visible(False)
        self.confirm_entry.set_visible(False)
        
        # Set login mode UI
        self._update_ui_mode()
        
        # Load last vault name if available
        try:
            last_vault = self.session.config.get_last_username()
            if last_vault:
                self.vault_entry.set_text(last_vault)
                self.password_entry.grab_focus()
            else:
                self.vault_entry.grab_focus()
        except:
            self.vault_entry.grab_focus()
    
    def _update_ui_mode(self):
        """Update UI based on current mode"""
        if self.is_register_mode:
            self.title_label.set_text("Create New Vault")
            self.subtitle_label.set_text("Set up your password manager")
            self.main_button.set_label("Create Vault")
            self.mode_button.set_label("Already have a vault? Sign In")
            self.confirm_label.set_visible(True)
            self.confirm_entry.set_visible(True)
        else:
            self.title_label.set_text("Welcome Back")
            self.subtitle_label.set_text("Open your secure vault")
            self.main_button.set_label("Open Vault")
            self.mode_button.set_label("Create New Vault")
            self.confirm_label.set_visible(False)
            self.confirm_entry.set_visible(False)
        
        self.error_label.set_text("")
    
    def _toggle_mode(self, button):
        """Toggle between login and register mode"""
        self.is_register_mode = not self.is_register_mode
        self._update_ui_mode()
    
    def _show_error(self, message):
        """Show error message"""
        self.error_label.set_text(message)
        self.spinner.stop()
        self._set_sensitive(True)
    
    def _set_sensitive(self, sensitive):
        """Enable/disable form inputs"""
        self.server_entry.set_sensitive(sensitive)
        self.vault_entry.set_sensitive(sensitive)
        self.password_entry.set_sensitive(sensitive)
        self.confirm_entry.set_sensitive(sensitive)
        self.main_button.set_sensitive(sensitive)
        self.mode_button.set_sensitive(sensitive)
    
    def _normalize_server_url(self, server_url):
        """Add https:// prefix if no protocol specified"""
        server_url = server_url.strip()
        if not server_url:
            return "https://server.upass.ch"
        
        # Only add https:// if no protocol specified
        if not server_url.startswith(('http://', 'https://')):
            server_url = f"https://{server_url}"
        
        return server_url
    
    def _validate_inputs(self):
        """Validate form inputs"""
        server_url = self.server_entry.get_text().strip()
        vault_name = self.vault_entry.get_text().strip()
        password = self.password_entry.get_text()
        
        if not server_url:
            self._show_error("Server is required")
            return False
        
        if not vault_name:
            self._show_error("Vault name is required")
            return False
        
        if not validate_username(vault_name):
            self._show_error("Invalid vault name (alphanumeric only, max 32 chars)")
            return False
        
        if not password:
            self._show_error("Password is required")
            return False
        
        if self.is_register_mode:
            confirm = self.confirm_entry.get_text()
            if password != confirm:
                self._show_error("Passwords do not match")
                return False
            
            if len(password) < 8:
                self._show_error("Password must be at least 8 characters")
                return False
        
        return True
    
    def _on_main_button_clicked(self, button):
        """Handle main button click"""
        if not self._validate_inputs():
            return
        
        self.error_label.set_text("")
        self.spinner.start()
        self._set_sensitive(False)
        
        # Run operation in background thread
        if self.is_register_mode:
            thread = threading.Thread(target=self._do_register_thread)
        else:
            thread = threading.Thread(target=self._do_login_thread)
        
        thread.daemon = True
        thread.start()
    
    def _do_login_thread(self):
        """Perform login in background thread"""
        server_url = self._normalize_server_url(self.server_entry.get_text())
        vault_name = self.vault_entry.get_text().strip()
        password = self.password_entry.get_text()
        
        try:
            # Create new session with the specified server URL
            session = UPassSession(server_url=server_url)
            
            # Mock password input for CLI
            import getpass
            old_getpass = getpass.getpass
            getpass.getpass = lambda prompt: password
            
            success = session.login(vault_name)
            
            if success:
                # Replace current session with the new one
                self.session = session
                GLib.idle_add(self._on_success)
            else:
                GLib.idle_add(self._show_error, "Invalid vault name or password")
        except Exception as e:
            GLib.idle_add(self._show_error, f"Login failed: {str(e)}")
        finally:
            getpass.getpass = old_getpass
    
    def _do_register_thread(self):
        """Perform registration in background thread"""
        server_url = self._normalize_server_url(self.server_entry.get_text())
        vault_name = self.vault_entry.get_text().strip()
        password = self.password_entry.get_text()
        
        try:
            # Create new session with the specified server URL
            session = UPassSession(server_url=server_url)
            
            # Mock password input for CLI
            import getpass
            old_getpass = getpass.getpass
            def mock_getpass(prompt):
                return password
            getpass.getpass = mock_getpass
            
            success = session.register(vault_name)
            
            if success:
                # Replace current session with the new one
                self.session = session
                GLib.idle_add(self._on_success)
            else:
                GLib.idle_add(self._show_error, "Vault creation failed. Name may already exist.")
        except Exception as e:
            GLib.idle_add(self._show_error, f"Registration failed: {str(e)}")
        finally:
            getpass.getpass = old_getpass
    
    def _on_success(self):
        """Handle successful login/registration"""
        self.spinner.stop()
        self.login_callback(self.session)
        return False