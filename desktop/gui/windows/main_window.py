import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import sys
import os

# Add CLI path for importing CLI modules
cli_path = os.path.join(os.path.dirname(__file__), '..', '..', 'cli')
if cli_path not in sys.path:
    sys.path.insert(0, cli_path)

from commands import UPassSession, VaultCommands
from utils import print_error, print_success, print_info
from widgets import VaultListWidget
from dialogs import EntryDialog, GenerateDialog, ServerSelectionDialog

def get_icon_path(icon_name):
    """Get the correct icon path for current environment (PNG for Windows, SVG for Linux)"""
    base_path = None
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundled environment
        base_path = os.path.join(sys._MEIPASS, 'gui', 'icons')
    else:
        # Development environment
        base_path = os.path.join(os.path.dirname(__file__), '..', 'icons')
    
    # Try PNG first (Windows compatibility), then SVG
    png_path = os.path.join(base_path, f'{icon_name}.png')
    if os.path.exists(png_path):
        return png_path
    
    svg_path = os.path.join(base_path, f'{icon_name}.svg')
    if os.path.exists(svg_path):
        return svg_path
    
    return None


class MainWindow(Gtk.ApplicationWindow):
    """Main application window"""
    
    def __init__(self, application, server_url=None):
        super().__init__(application=application)
        
        # Import version
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from version import get_version
        
        self.set_title(f"UPass v{get_version()} - Password Manager")
        self.set_default_size(900, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Set application icon
        self._set_icon()
        
        # Load custom theme
        self._load_theme()
        
        # Add window style
        self.get_style_context().add_class("upass-window")
        
        # Initialize session with custom server
        self.session = UPassSession(server_url=server_url)
        self.vault_commands = VaultCommands(self.session)
        
        # Setup UI
        self._setup_ui()
        
        # Show all widgets
        self.show_all()
        
        # Check if already authenticated
        if self.session.authenticated:
            self._show_vault_view()
        else:
            self._show_login_view()
    
    def _set_icon(self):
        """Set application icon from project root"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'icon.png')
            if os.path.exists(icon_path):
                self.set_icon_from_file(icon_path)
                # Hide the icon from the header bar
                self.set_show_menubar(False)
                settings = Gtk.Settings.get_default()
                settings.set_property("gtk-decoration-layout", "menu:close")
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")
    
    def _load_theme(self):
        """Load custom CSS theme"""
        try:
            css_provider = Gtk.CssProvider()
            theme_path = os.path.join(os.path.dirname(__file__), '..', 'theme.css')
            css_provider.load_from_path(theme_path)
            
            screen = Gdk.Screen.get_default()
            style_context = Gtk.StyleContext()
            style_context.add_provider_for_screen(
                screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Warning: Could not load theme: {e}")
    
    def _setup_ui(self):
        """Setup main UI components"""
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_box)
        
        # Header bar
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(False)
        self.header_bar.set_title("UPass")
        self.set_titlebar(self.header_bar)
        
        # Server selection button
        self.server_button = Gtk.Button()
        self.server_button.set_tooltip_text("Select UPass Server")
        server_icon = Gtk.Image.new_from_icon_name("network-server", Gtk.IconSize.BUTTON)
        self.server_button.set_image(server_icon)
        self.server_button.connect('clicked', self._on_server_button_clicked)
        self.header_bar.pack_start(self.server_button)
        
        # Update server button label
        self._update_server_button()
        
        # Stack for switching views
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.main_box.pack_start(self.stack, True, True, 0)
        
        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.main_box.pack_start(self.status_bar, False, False, 0)
        self.status_context = self.status_bar.get_context_id("status")
    
    def _show_login_view(self):
        """Show login/register view"""
        # Check if login widget already exists
        login_widget = self.stack.get_child_by_name("login")
        if not login_widget:
            # Create new login widget only if it doesn't exist
            from windows.login_window import LoginWindow
            login_widget = LoginWindow(self._on_login_success, self.session, 
                                     initial_server_url=self.session.config.server_url)
            login_widget.show_all()
            self.stack.add_named(login_widget, "login")
        
        self.stack.set_visible_child_name("login")
        self.header_bar.set_subtitle(None)
        
        # Clear header bar buttons
        for child in self.header_bar.get_children():
            if isinstance(child, Gtk.Button):
                self.header_bar.remove(child)
        
        # Add close button for login view
        close_button = Gtk.Button()
        try:
            close_icon_path = get_icon_path('close')
            if close_icon_path:
                close_icon = Gtk.Image.new_from_file(close_icon_path)
                close_button.set_image(close_icon)
            else:
                close_button.set_label("×")
        except:
            close_button.set_label("×")
        
        close_button.set_tooltip_text("Close")
        close_button.connect("clicked", self._on_close_clicked)
        close_button.show()
        self.header_bar.pack_end(close_button)
    
    def _show_vault_view(self):
        """Show vault entries view"""
        # Create vault view if not exists
        if not self.stack.get_child_by_name("vault"):
            vault_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            vault_box.set_margin_top(6)
            vault_box.set_margin_bottom(6)
            vault_box.set_margin_left(6)
            vault_box.set_margin_right(6)
            
            # Search bar
            search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            
            search_entry = Gtk.SearchEntry()
            search_entry.set_placeholder_text("Search entries...")
            search_entry.connect("search-changed", self._on_search_changed)
            search_box.pack_start(search_entry, True, True, 0)
            
            vault_box.pack_start(search_box, False, False, 0)
            
            # Vault list
            self.vault_list = VaultListWidget(self.session, self.vault_commands)
            self.vault_list.connect("entry-selected", self._on_entry_selected)
            self.vault_list.connect("entry-copied", self._on_entry_copied)
            
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(self.vault_list)
            vault_box.pack_start(scrolled, True, True, 0)
            
            vault_box.show_all()
            self.stack.add_named(vault_box, "vault")
            self.search_entry = search_entry
        
        # Update header bar
        self.header_bar.set_subtitle(f"Vault: {self.session.username}")
        
        # Add header bar buttons
        for child in self.header_bar.get_children():
            if isinstance(child, Gtk.Button):
                self.header_bar.remove(child)
        
        # Add button with custom icon
        add_button = Gtk.Button()
        try:
            add_icon_path = get_icon_path('add')
            if add_icon_path:
                add_icon = Gtk.Image.new_from_file(add_icon_path)
                add_button.set_image(add_icon)
            else:
                add_button.set_label("+")
        except:
            add_button.set_label("+")
        
        add_button.set_tooltip_text("Add new entry")
        add_button.connect("clicked", self._on_add_clicked)
        add_button.show()
        self.header_bar.pack_start(add_button)
        
        # Generate button with custom icon
        gen_button = Gtk.Button()
        try:
            gen_icon_path = get_icon_path('generate')
            if gen_icon_path:
                gen_icon = Gtk.Image.new_from_file(gen_icon_path)
                gen_button.set_image(gen_icon)
            else:
                gen_button.set_label("Gen")
        except:
            gen_button.set_label("Gen")
        
        gen_button.set_tooltip_text("Generate password") 
        gen_button.connect("clicked", self._on_generate_clicked)
        gen_button.show()
        self.header_bar.pack_start(gen_button)
        
        # Refresh button with custom icon
        refresh_button = Gtk.Button()
        try:
            refresh_icon_path = get_icon_path('refresh')
            if refresh_icon_path:
                refresh_icon = Gtk.Image.new_from_file(refresh_icon_path)
                refresh_button.set_image(refresh_icon)
            else:
                refresh_button.set_label("↻")
        except:
            refresh_button.set_label("↻")
        
        refresh_button.set_tooltip_text("Refresh vault")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        refresh_button.show()
        self.header_bar.pack_start(refresh_button)
        
        # Window controls - close/maximize/minimize buttons (rightmost)
        # Close button with custom icon
        close_button = Gtk.Button()
        try:
            close_icon_path = get_icon_path('close')
            if close_icon_path:
                close_icon = Gtk.Image.new_from_file(close_icon_path)
                close_button.set_image(close_icon)
            else:
                close_button.set_label("×")
        except:
            close_button.set_label("×")
        
        close_button.set_tooltip_text("Close")
        close_button.connect("clicked", self._on_close_clicked)
        close_button.show()
        self.header_bar.pack_end(close_button)
        
        # Maximize button with custom icon
        maximize_button = Gtk.Button()
        try:
            maximize_icon_path = get_icon_path('maximize')
            if maximize_icon_path:
                maximize_icon = Gtk.Image.new_from_file(maximize_icon_path)
                maximize_button.set_image(maximize_icon)
            else:
                maximize_button.set_label("⛶")
        except:
            maximize_button.set_label("⛶")
        
        maximize_button.set_tooltip_text("Maximize/Restore")
        maximize_button.connect("clicked", self._on_maximize_clicked)
        maximize_button.show()
        self.header_bar.pack_end(maximize_button)
        
        # Minimize button with custom icon
        minimize_button = Gtk.Button()
        try:
            minimize_icon_path = get_icon_path('minimize')
            if minimize_icon_path:
                minimize_icon = Gtk.Image.new_from_file(minimize_icon_path)
                minimize_button.set_image(minimize_icon)
            else:
                minimize_button.set_label("_")
        except:
            minimize_button.set_label("_")
        
        minimize_button.set_tooltip_text("Minimize")
        minimize_button.connect("clicked", self._on_minimize_clicked)
        minimize_button.show()
        self.header_bar.pack_end(minimize_button)
        
        # Add invisible spacing
        spacer = Gtk.Box()
        spacer.set_size_request(15, -1)
        spacer.show()
        self.header_bar.pack_end(spacer)
        
        # Logout button with custom icon
        logout_button = Gtk.Button()
        try:
            logout_icon_path = get_icon_path('logout')
            if logout_icon_path:
                logout_icon = Gtk.Image.new_from_file(logout_icon_path)
                logout_button.set_image(logout_icon)
            else:
                logout_button.set_label("Logout")
        except:
            logout_button.set_label("Logout")
        
        logout_button.set_tooltip_text("Logout")
        logout_button.connect("clicked", self._on_logout_clicked)
        logout_button.show()
        self.header_bar.pack_end(logout_button)
        
        # Delete vault button with custom icon
        delete_button = Gtk.Button()
        try:
            delete_icon_path = get_icon_path('delete')
            if delete_icon_path:
                delete_icon = Gtk.Image.new_from_file(delete_icon_path)
                delete_button.set_image(delete_icon)
            else:
                delete_button.set_label("🗑")
        except:
            delete_button.set_label("🗑")
        
        delete_button.set_tooltip_text("Delete Vault Permanently")
        delete_button.connect("clicked", self._on_delete_vault_clicked)
        delete_button.show()
        self.header_bar.pack_end(delete_button)
        
        # Show vault view
        self.stack.set_visible_child_name("vault")
        self.vault_list.refresh()
        
        # Focus search
        self.search_entry.grab_focus()
    
    def _on_login_success(self, updated_session=None):
        """Handle successful login"""
        # Update session if provided
        if updated_session:
            self.session = updated_session
            self.vault_commands = VaultCommands(self.session)
        else:
            # Fallback: Get the updated session from the login widget
            login_widget = self.stack.get_child_by_name("login")
            if login_widget and hasattr(login_widget, 'session'):
                self.session = login_widget.session
                self.vault_commands = VaultCommands(self.session)
        
        # Remove existing vault view to force recreation with new session
        vault_widget = self.stack.get_child_by_name("vault")
        if vault_widget:
            self.stack.remove(vault_widget)
        
        self._show_vault_view()
        self.show_message(f"Logged into vault '{self.session.username}' successfully!", Gtk.MessageType.INFO)
    
    def _on_search_changed(self, entry):
        """Handle search text change"""
        search_text = entry.get_text()
        self.vault_list.set_filter(search_text)
    
    def _on_entry_selected(self, widget, entry):
        """Handle entry double-click"""
        dialog = EntryDialog(self, self.session, self.vault_commands, entry)
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self.vault_list.refresh()
            self.show_message("Entry updated", Gtk.MessageType.INFO)
    
    def _on_entry_copied(self, widget, entry_note):
        """Handle password copied"""
        self.show_message(f"Password for '{entry_note}' copied to clipboard", Gtk.MessageType.INFO)
    
    def _on_add_clicked(self, button):
        """Handle add button click"""
        dialog = EntryDialog(self, self.session, self.vault_commands)
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self.vault_list.refresh()
            self.show_message("Entry added", Gtk.MessageType.INFO)
    
    def _on_generate_clicked(self, button):
        """Handle generate button click"""
        dialog = GenerateDialog(self, self.session.crypto)
        dialog.run()
        dialog.destroy()
    
    def _on_refresh_clicked(self, button):
        """Handle refresh button click"""
        try:
            # Fetch latest vault from server
            vault_blob = self.session.api.get_vault()
            if vault_blob:
                vault_data = self.session.crypto.decrypt_vault(vault_blob)
                self.session.vault.from_list(vault_data)
                # Clear search filter and refresh
                self.search_entry.set_text("")
                self.vault_list.set_filter("")
                self.vault_list.refresh()
                self.show_message(f"Vault refreshed - {len(self.session.vault.entries)} entries", Gtk.MessageType.INFO)
            else:
                # Empty vault
                self.session.vault.clear()
                self.search_entry.set_text("")
                self.vault_list.set_filter("")
                self.vault_list.refresh()
                self.show_message("Vault refreshed - empty", Gtk.MessageType.INFO)
        except Exception as e:
            self.show_message(f"Failed to refresh: {str(e)}", Gtk.MessageType.ERROR)
    
    def _on_delete_vault_clicked(self, button):
        """Handle delete vault button click"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete Vault Permanently?"
        )
        dialog.format_secondary_text("Are you sure you want to permanently delete your entire vault? This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                if self.session.delete_vault():
                    # Remove existing login widget to ensure clean state
                    login_widget = self.stack.get_child_by_name("login")
                    if login_widget:
                        self.stack.remove(login_widget)
                    
                    self._show_login_view()
                    self.show_message("Vault deleted permanently", Gtk.MessageType.INFO)
                else:
                    self.show_message("Failed to delete vault", Gtk.MessageType.ERROR)
            except Exception as e:
                self.show_message(f"Failed to delete vault: {str(e)}", Gtk.MessageType.ERROR)
    
    def _on_logout_clicked(self, button):
        """Handle logout button click"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Logout from UPass?"
        )
        dialog.format_secondary_text("You will need to enter your master password to login again.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.session.logout()
            
            # Remove existing login widget to ensure clean state
            login_widget = self.stack.get_child_by_name("login")
            if login_widget:
                self.stack.remove(login_widget)
            
            self._show_login_view()
            self.show_message("Logged out successfully", Gtk.MessageType.INFO)
    
    def _update_server_button(self):
        """Update server button with current server info"""
        from urllib.parse import urlparse
        parsed = urlparse(self.session.config.server_url)
        server_name = parsed.netloc
        
        # Create button label with server
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Icon
        server_icon = Gtk.Image.new_from_icon_name("network-server", Gtk.IconSize.BUTTON)
        button_box.pack_start(server_icon, False, False, 0)
        
        # Server name
        server_label = Gtk.Label(label=server_name)
        button_box.pack_start(server_label, False, False, 0)
        
        # Remove old child and add new one
        old_child = self.server_button.get_child()
        if old_child:
            self.server_button.remove(old_child)
        
        self.server_button.add(button_box)
        button_box.show_all()
    
    def _on_server_button_clicked(self, button):
        """Handle server selection button click"""
        dialog = ServerSelectionDialog(self, current_server=self.session.config.server_url)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            selected_server = dialog.get_selected_server()
            if selected_server and selected_server != self.session.config.server_url:
                # Server changed, need to restart session
                self._change_server(selected_server)
        
        dialog.destroy()
    
    def _change_server(self, new_server_url):
        """Change to a different server"""
        # Logout current session
        if self.session.authenticated:
            self.session.logout()
        
        # Create new session with different server
        self.session = UPassSession(server_url=new_server_url)
        self.vault_commands = VaultCommands(self.session)
        
        # Update UI
        self._update_server_button()
        
        # Remove existing login widget to ensure clean state
        login_widget = self.stack.get_child_by_name("login")
        if login_widget:
            self.stack.remove(login_widget)
        
        # Show login view for new server
        self._show_login_view()
        self.show_message(f"Switched to server: {new_server_url}", Gtk.MessageType.INFO)
    
    def _on_minimize_clicked(self, button):
        """Handle minimize button click"""
        self.iconify()
    
    def _on_maximize_clicked(self, button):
        """Handle maximize/restore button click"""
        if self.is_maximized():
            self.unmaximize()
        else:
            self.maximize()
    
    def _on_close_clicked(self, button):
        """Handle close button click"""
        self.close()

    def show_message(self, message, message_type):
        """Show status message"""
        self.status_bar.pop(self.status_context)
        self.status_bar.push(self.status_context, message)
        
        # Auto-clear after 3 seconds
        GLib.timeout_add_seconds(3, lambda: self.status_bar.pop(self.status_context))